# opteryx.app

**Query your data, where it lives.**

[Opteryx](https://opteryx.app/) brings SQL analytics to your data without moving
it — fast, simple and secure.

This repository is the **public home for issues, planning and documentation for
opteryx.app**. It contains no service code; the platform is built from the open
source projects listed below, and this repo is where work across them is tracked
and discussed.

- 🌐 Website — <https://opteryx.app/>
- 📖 Documentation — <https://docs.opteryx.app/>
- 🐞 Issues — <https://github.com/mabel-dev/opteryx.app/issues>
- 🔀 Open pull requests across the org — [search view](https://github.com/search?q=org%3Amabel-dev+is%3Apr+state%3Aopen&type=pullrequests)

## What this repo is for

| Use it for | Use the project repo instead |
| --- | --- |
| Bugs and feature requests for the hosted opteryx.app service | Bugs in the query engine, drivers or clients |
| Roadmap, planning and cross-repo tracking issues | Code changes and pull requests |
| Questions about the platform as a whole | Questions specific to one library |
| Documentation about how the pieces fit together | Reference docs for a single project |

If you are not sure which repo something belongs in, open it here and we will
move it.

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to raise issues and contribute.

## The projects

Opteryx is developed in the open under the
[mabel-dev](https://github.com/mabel-dev) organisation.

### Query engine and core

| Repository | Description |
| --- | --- |
| [opteryx](https://github.com/mabel-dev/opteryx) | 🦖 SQL-on-everything query engine — execute SQL over multiple databases and file formats |
| [opteryx-core](https://github.com/mabel-dev/opteryx-core) | ⚙️ Query engine core and the Rugo file driver |
| [opteryx-catalog](https://github.com/mabel-dev/opteryx-catalog) | 📚 Opteryx Cloud Catalog |
| [rugo.dev](https://github.com/mabel-dev/rugo.dev) | Light-weight Parquet and JSON library for Python |

### Clients, drivers and tools

| Repository | Description |
| --- | --- |
| [opteryx-sqlalchemy](https://github.com/mabel-dev/opteryx-sqlalchemy) | SQLAlchemy dialect for Opteryx |
| [terraform-provider-opteryx](https://github.com/mabel-dev/terraform-provider-opteryx) | Terraform provider for Opteryx resources |
| [vscode-parquet-inspector](https://github.com/mabel-dev/vscode-parquet-inspector) | Rugo Parquet Inspector extension for VS Code |
| [opteryx-upload](https://github.com/mabel-dev/opteryx-upload) | Data upload tooling for opteryx.app |

### Documentation sites

| Repository | Description |
| --- | --- |
| [docs.opteryx.app](https://github.com/mabel-dev/docs.opteryx.app) | Documentation for the opteryx.app platform |
| [opteryx.dev](https://github.com/mabel-dev/opteryx.dev) | 🌐 Documentation site for the Opteryx query engine |
| [rugo.opteryx.dev](https://github.com/mabel-dev/rugo.opteryx.dev) | Documentation site for Rugo |
| [opteryx.app](https://github.com/mabel-dev/opteryx.app) | 📦 This repository |

### Supporting libraries

| Repository | Description |
| --- | --- |
| [orso](https://github.com/mabel-dev/orso) | 🐻 Row-based Python DataFrame library |
| [ossis](https://github.com/mabel-dev/ossis) | Schema library |
| [mabel](https://github.com/mabel-dev/mabel) | 😊 Platform for authoring data processing systems |
| [gimbal-lock](https://github.com/mabel-dev/gimbal-lock) | Opteryx's performance benchmarking tool |
| [s1](https://github.com/mabel-dev/s1) | A minimal AWS S3 emulator |

The full list is on the
[organisation page](https://github.com/orgs/mabel-dev/repositories).

## Licence

Apache License 2.0 — see [LICENSE](LICENSE).
