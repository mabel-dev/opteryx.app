"""
Turn a Fides JSON report into open issues on a single tracking repository.

Fides has no GitHub API surface of its own - it emits workflow annotations and
exits non-zero (`run.py:emit_github_annotation`). Annotations die with the run,
so a secret found by the 6:43am cron on a repository nobody is looking at
leaves nothing behind. This script is the missing half: it files the finding
where the fleet already watches for failures, alongside the healthchecks.io
GitHub-issue channel the Pi jobs use (`xb500.opteryx/pi_jobs/README.md`).

Three things it is careful about:

* **The secret never reaches the issue.** Only the rule, its description, the
  file and the line go into the body. Fides redacts matched values, but even
  the redaction is left out - an issue is a permanent, searchable, often more
  widely readable artefact than the job log, and a tracker full of leaked
  credentials is worse than the leak it reports.
* **A persisting finding does not re-file every run.** The scan runs on every
  push to main and daily on cron. Issues are keyed by a fingerprint over
  (source repository, rule, file), not by line number, so a finding that
  merely moves down the file stays one issue.
* **A fixed finding closes itself.** Every run reconciles the full set for the
  scanned repository, so the tracker reflects the current state of main rather
  than accumulating history.

Deduplication reads the open issue list directly rather than the search API:
search is an eventually-consistent index, and a push-triggered run finishing
seconds after the last one would not see its own issue yet.
"""

import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List, Optional

# GITHUB_API_URL is set by Actions; the default keeps the script runnable
# outside a workflow.
API = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")

# Findings below this are reported by Fides but do not fail a scan
# (`run.py:WARN_IMPORTANCES`), and allowlisted ones are public by design.
# Neither is worth an issue.
ACTIONABLE_SEVERITY = "error"

LABEL = "secret-scan"
LABEL_COLOR = "b60205"
LABEL_DESCRIPTION = "Opened by the Fides secret scanner"

# Every title this script owns starts here, so the reconcile step can tell its
# own issues from anything else carrying the label.
TITLE_PREFIX = "[secret-scan]"


def api(
    token: str, method: str, path: str, body: Optional[Dict[str, Any]] = None
) -> Any:
    request = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "fides-issue-sync",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read()
        return json.loads(raw) if raw else None


def fingerprint(source_repo: str, rule: str, file_name: str) -> str:
    """
    Identify a finding by where it lives, not by which line it is on.

    Line numbers move whenever anything above them changes; keying on them
    would file a fresh issue for an unchanged secret the first time someone
    adds an import.
    """
    digest = hashlib.sha256(f"{source_repo}|{rule}|{file_name}".encode())
    return digest.hexdigest()[:12]


def title_for(source_repo: str, rule: str, file_name: str, fp: str) -> str:
    return f"{TITLE_PREFIX} {source_repo}: {rule} in {file_name} ({fp})"


def locations_of(group: List[Dict[str, Any]]) -> List[tuple]:
    return sorted({(f["line"], f["column"]) for f in group})


def location_signature(group: List[Dict[str, Any]]) -> str:
    return ",".join(f"{line}:{column}" for line, column in locations_of(group))


MARKER = re.compile(r"<!-- fides-fingerprint: \S+ at ([^>]*?) -->")


def signature_in(body: Optional[str]) -> Optional[str]:
    """
    Recover the location signature an existing issue was written from.

    The rest of the body carries the commit and the run URL, which differ on
    every scan - comparing whole bodies would edit every issue on every run
    and turn the tracker into a change log.
    """
    match = MARKER.search(body or "")
    return match.group(1).strip() if match else None


def body_for(
    group: List[Dict[str, Any]], source_repo: str, sha: str, run_url: str, fp: str
) -> str:
    """
    Describe the finding well enough to act on without reproducing any part of
    the credential. `match`, `match_length` and `context` from the report are
    deliberately not read here.
    """
    first = group[0]
    locations = locations_of(group)
    lines = "\n".join(
        f"- `{first['file']}:{line}:{column}`" for line, column in locations
    )
    return f"""The Fides secret scanner matched a rule on `{source_repo}` main.

| | |
|---|---|
| Repository | [`{source_repo}`](https://github.com/{source_repo}) |
| Rule | `{first['rule']}` |
| Description | {first['description']} |
| Importance | `{first['importance']}` |
| Commit | [`{sha[:8]}`](https://github.com/{source_repo}/commit/{sha}) |
| Scan run | {run_url} |

### Where

{lines}

### What to do

1. Confirm it is a real credential and not a fixture. If it is public by
   design, add it to the `SECRETS00` allowlist rule in
   [joocer/fides](https://github.com/joocer/fides/tree/main/rules) rather
   than silencing the scan.
2. **Rotate it first, then remove it.** Git history keeps the old commit; the
   removal commit does not un-leak anything on its own.
3. This issue closes itself on the next scan of `{source_repo}` main
   once the rule no longer matches that file.

> The matched value is not recorded here, redacted or otherwise. Read it from
> the file above, not from this tracker.

<!-- fides-fingerprint: {fp} at {location_signature(group)} -->
"""


def ensure_label(token: str, issue_repo: str) -> None:
    try:
        api(
            token,
            "POST",
            f"/repos/{issue_repo}/labels",
            {
                "name": LABEL,
                "color": LABEL_COLOR,
                "description": LABEL_DESCRIPTION,
            },
        )
    except urllib.error.HTTPError as error:
        # 422 is "already exists", which is the common case after the first run.
        if error.code != 422:
            raise


def open_issues(token: str, issue_repo: str) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    page = 1
    while True:
        batch = api(
            token,
            "GET",
            f"/repos/{issue_repo}/issues"
            f"?state=open&labels={LABEL}&per_page=100&page={page}",
        )
        if not batch:
            return issues
        # The issues endpoint returns pull requests too; they are not ours.
        issues.extend(item for item in batch if "pull_request" not in item)
        if len(batch) < 100:
            return issues
        page += 1


def main() -> int:
    report_path = os.environ["FIDES_REPORT"]
    issue_repo = os.environ["FIDES_ISSUE_REPO"]
    source_repo = os.environ["FIDES_SOURCE_REPO"]
    sha = os.environ.get("FIDES_SHA", "")
    run_url = os.environ.get("FIDES_RUN_URL", "")
    token = os.environ.get("FIDES_ISSUE_TOKEN", "")
    dry_run = os.environ.get("FIDES_DRY_RUN", "").lower() == "true"

    if not token and not dry_run:
        # A repository that has not been granted the org PAT should not fail
        # its scan over it - the scan result itself is unaffected.
        print("No FIDES_ISSUE_TOKEN available - not filing issues.")
        return 0

    if not os.path.exists(report_path):
        # The scan did not get far enough to write one. Its own failure is
        # already the visible signal; inventing issues here would be noise.
        print(f"No report at {report_path} - nothing to reconcile.")
        return 0

    with open(report_path, encoding="utf-8") as handle:
        report = json.load(handle)

    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for finding in report.get("findings", []):
        if finding.get("severity") != ACTIONABLE_SEVERITY:
            continue
        groups[fingerprint(source_repo, finding["rule"], finding["file"])].append(
            finding
        )

    print(f"{len(groups)} distinct finding(s) on {source_repo}.")

    if dry_run:
        for fp, group in sorted(groups.items()):
            print(f"  would file: {title_for(source_repo, group[0]['rule'], group[0]['file'], fp)}")
        return 0

    ensure_label(token, issue_repo)
    existing = {issue["title"]: issue for issue in open_issues(token, issue_repo)}

    wanted = {}
    for fp, group in sorted(groups.items()):
        wanted[title_for(source_repo, group[0]["rule"], group[0]["file"], fp)] = (
            fp,
            group,
        )

    for title, (fp, group) in wanted.items():
        if title in existing:
            issue = existing[title]
            if signature_in(issue.get("body")) != location_signature(group):
                # The finding is the same one; only where it sits has moved.
                # Refreshing keeps the line numbers in the issue honest
                # instead of pointing at wherever the secret used to be.
                api(
                    token,
                    "PATCH",
                    f"/repos/{issue_repo}/issues/{issue['number']}",
                    {"body": body_for(group, source_repo, sha, run_url, fp)},
                )
                print(f"  refreshed: #{issue['number']} {title}")
            else:
                print(f"  already open: #{issue['number']} {title}")
            continue
        issue = api(
            token,
            "POST",
            f"/repos/{issue_repo}/issues",
            {
                "title": title,
                "body": body_for(group, source_repo, sha, run_url, fp),
                "labels": [LABEL],
            },
        )
        print(f"  filed: #{issue['number']} {title}")

    # Only this repository's issues are reconciled - another repository's
    # findings are not in this report and must not be read as resolved.
    mine = f"{TITLE_PREFIX} {source_repo}: "
    for title, issue in existing.items():
        if not title.startswith(mine) or title in wanted:
            continue
        api(
            token,
            "POST",
            f"/repos/{issue_repo}/issues/{issue['number']}/comments",
            {
                "body": f"No longer matched by the scan of "
                f"[`{source_repo}@{sha[:8]}`]"
                f"(https://github.com/{source_repo}/commit/{sha}). "
                f"Closing.\n\nRotate the credential if that has not been done "
                f"already - removing it from the working tree does not remove "
                f"it from history.\n\n{run_url}"
            },
        )
        api(
            token,
            "PATCH",
            f"/repos/{issue_repo}/issues/{issue['number']}",
            {"state": "closed", "state_reason": "completed"},
        )
        print(f"  closed: #{issue['number']} {title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
