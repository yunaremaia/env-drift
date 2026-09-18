# env-drift

Detect cross-environment configuration drift — when `.env.development`, `.env.staging`, and `.env.production` diverge in unexpected ways.

## Problem

Modern applications maintain multiple environment files (`.env.development`, `.env.staging`, `.env.production`). Common failure modes:

- **Missing keys** in production that exist in development (causes `undefined` values in prod)
- **Divergent secrets** where staging and production should share the same keys (database URLs, API endpoints)
- **Inconsistent values** where the same key has different formats across environments
- **Orphaned keys** that exist in prod but no longer in any other environment (dead config, security risk)

Existing tools validate *individual* files (`dotenv-linter`, `dotenv-validator`) but do **not** compare across environments. This leaves drift undetected until a deploy breaks.

## Solution

`env-drift` scans a project for `.env.*` files and reports:

| Check | What it catches |
|-------|----------------|
| Missing keys | Key in `.env.development` but not in `.env.production` |
| Divergent secrets | Key marked as "shared" in config but values differ across envs |
| Orphaned keys | Key in `.env.production` missing from all other envs |
| Format mismatch | Same key with inconsistent value formats (e.g., `true` vs `True`) |
| Empty values | Required key present but empty in one environment |

### Usage

```bash
# Scan current directory for .env.* drift
env-drift scan

# Define which keys must be consistent across environments
# (in pyproject.toml or .env-drift.toml)
[tool.env-drift]
shared-keys = ["DATABASE_URL", "REDIS_URL", "LOG_LEVEL"]
required-in-prod = ["SECRET_KEY", "DATABASE_URL"]

# Run with config
env-drift scan --config .env-drift.toml

# Output formats
env-drift scan --format json   # CI-friendly
env-drift scan --format sarif  # GitHub Code Scanning integration
```

### Exit Codes

- `0` — no drift detected
- `1` — drift detected (CI fail)
- `2` — config error

## Stack

- **Language:** Python 3.11+
- **Parser:** Pure stdlib (`os.environ` compatible, no `dotenv` runtime dependency)
- **Config:** `pyproject.toml` (PEP 621) or standalone `.env-drift.toml`
- **Output:** Terminal, JSON, SARIF
- **Tests:** `pytest`

## Roadmap

- [ ] Core scanner: missing/divergent/orphan/format checks
- [ ] Config-driven shared-key enforcement
- [ ] SARIF output for GitHub Advanced Security
- [ ] Auto-fix: synchronize missing keys from reference env
- [ ] Git pre-commit hook integration
- [ ] Diff mode: compare two specific envs
- [ ] Secret masking in output (don't print values, just keys)
- [ ] Multi-language support (`.envrc`, `config.yaml` profiles)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

Please follow the existing test-first pattern and run `pytest` before submitting.

## License

MIT

## Project Links

- Repository: https://github.com/yunaremaia/env-drift
- Issues: https://github.com/yunaremaia/env-drift/issues
