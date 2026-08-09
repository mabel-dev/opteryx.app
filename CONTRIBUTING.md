# Contributing

Thanks for taking an interest in Opteryx. Contributions of all kinds are
welcome — bug reports, documentation, ideas and code.

This repository ([opteryx.app](https://github.com/mabel-dev/opteryx.app)) is
where work on the opteryx.app platform is tracked. It holds issues, planning and
documentation rather than service code, so most code contributions belong in one
of the [project repositories](README.md#the-projects).

## Where to raise things

| What | Where |
| --- | --- |
| Bug in the hosted opteryx.app service | [Issues on this repo](https://github.com/mabel-dev/opteryx.app/issues) |
| Feature request for the platform | [Issues on this repo](https://github.com/mabel-dev/opteryx.app/issues) |
| Bug or feature in the query engine | [mabel-dev/opteryx](https://github.com/mabel-dev/opteryx/issues) |
| Bug or feature in another project | That project's own issue tracker |
| Something that spans several repos | Here, as a tracking issue linking to the others |
| A security vulnerability | **Do not open a public issue** — see [Security issues](#security-issues) |

If you pick the wrong place, that is fine — we will move it.

## Raising an issue

Before opening an issue, please search
[existing issues](https://github.com/mabel-dev/opteryx.app/issues?q=is%3Aissue)
including closed ones.

A good bug report includes:

- What you did, in enough detail that we can repeat it — the SQL, the API call,
  or the steps in the UI
- What you expected to happen
- What actually happened, including the full error message and any request or
  correlation ID
- When it happened (with a timezone) and which environment
- Versions of any client libraries involved

A good feature request explains the problem you are trying to solve, not only
the solution you have in mind. Real examples help a lot.

## Labels

Issues are triaged with these labels:

- `bug` — something isn't working
- `enhancement` — new feature or request
- `documentation` — improvements or additions to documentation
- `question` — further information is requested
- `good first issue` — a sensible place to start if you are new
- `help wanted` — extra attention is needed
- `severity:critical`, `severity:error` — impact of a defect
- `production`, `platform-failure`, `alerting-probe` — operational issues

## Contributing code

Code changes are made in the project repositories, not here. The general flow:

1. Open an issue first for anything more than a small fix, so the approach can
   be agreed before you spend time on it.
2. Fork the repository and create a branch off `main`.
3. Make your change, keeping it focused — one concern per pull request.
4. Add or update tests, and make sure the existing suite passes.
5. Follow the formatting and linting set up in that repo (most Python projects
   use `ruff` and `isort`, line length 100).
6. Open a pull request against `main`, describing what changed and why, and
   linking the issue it closes.

Pull requests need a green CI run and a review before they can be merged.

## Documentation

Documentation lives with the thing it documents:

- Platform documentation — [docs.opteryx.app](https://github.com/mabel-dev/docs.opteryx.app)
- Query engine documentation — [opteryx.dev](https://github.com/mabel-dev/opteryx.dev)
- Rugo documentation — [rugo.opteryx.dev](https://github.com/mabel-dev/rugo.opteryx.dev)

Corrections to documentation are always welcome and are a good first
contribution.

## Security issues

Please do not report security vulnerabilities through public issues, pull
requests or discussions. Instead, use GitHub's
[private vulnerability reporting](https://github.com/mabel-dev/opteryx.app/security/advisories/new)
so the problem can be fixed before it is made public.

Include what you found, how to reproduce it, and what an attacker could do with
it. You will get an acknowledgement, and we will keep you updated as it is
resolved.

## Conduct

Be decent to each other. Assume good faith, keep discussion focused on the work,
and accept that maintainers may decline a change without it being a judgement of
you. Behaviour that makes the project unwelcoming — harassment, personal
attacks, or discriminatory language — is not tolerated, and maintainers may
remove comments, issues or contributors that cross that line.

## Licence

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE), the same licence that covers the projects.
