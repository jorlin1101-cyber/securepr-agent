# Changelog

All notable public changes to SecurePR Agent are documented in this file.

## [Unreleased]

### Added

- A model-backed Agent Runtime with Lead, Security, Correctness/Reliability, and Critic roles.
- Context budgeting, repository tools, isolated memory recall, execution ledgers, and finding gates.
- Declarative `SKILL.md` Agent Skills with tenant-scoped evolution, replay evaluation, activation, and rollback.
- Prompt-evolution proofs, real-PR evaluation gates, verified unified patches, and before/after test evidence.
- Dashboard views for run mode, model usage, collaboration traces, task feedback, and Skill evolution.

### Changed

- Replaced LangGraph and executable Python review Skills with the built-in runtime and declarative Agent Skills.
- Kept authentication secure by default and retained output sanitization and semantic finding deduplication.
- SQLite connections now close reliably after each transaction, including on Windows.

## [0.3.0] - 2026-08-12

### Added

- GitHub Pull Request webhook review and optional review-comment publishing.
- Multi-agent review, conservative repair branches, persistent task state, and the web dashboard.
- Prompt evaluation, holdout regression gates, version activation, and rollback.
- PostgreSQL, Redis Streams, RBAC, audit logging, tracing, metrics, and alerts.

### Safety

- Destructive test guidance is filtered before it reaches reports or Pull Request comments.
- Semantically duplicated findings from local and model reviewers are merged.
- Repair branches pass compile and optional test verification before publication.

### Validation

- Python 3.11 compile checks and the complete unit-test suite run in GitHub Actions.
- Ruff static checks and Gitleaks secret scanning protect new changes.

[0.3.0]: https://github.com/jorlin1101-cyber/securepr-agent/releases/tag/v0.3.0
