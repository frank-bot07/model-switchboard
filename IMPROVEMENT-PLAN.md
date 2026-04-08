# Model Switchboard — Improvement Plan

**Goal**: Turn this into a standalone open-source product on GitHub.  
**Current state**: Production-ready OpenClaw skill (v3.0, security-audited). All critical safety features complete. Tightly coupled to OpenClaw internals.

---

## Executive Summary

Model Switchboard is a well-architected, fail-closed model configuration manager. The security baseline is strong (v3.0 Opus audit passed), the core engine is solid, and there are zero external dependencies. The primary work to go standalone is **decoupling from OpenClaw** and adding **tests + docs**.

Priority order: Decoupling → Docs → Tests → Polish → Features.

---

## Phase 1: Decoupling from OpenClaw (Blocker for Standalone)

Everything else is blocked until this is done.

### 1.1 Configurable Paths

Replace all hardcoded `~/.openclaw/` paths with environment variable overrides.

**switchboard.sh**:
```bash
# Replace hardcoded values with:
SWITCHBOARD_BASE="${SWITCHBOARD_BASE:-$HOME/.openclaw}"
OPENCLAW_CONFIG="${SWITCHBOARD_CONFIG:-$SWITCHBOARD_BASE/openclaw.json}"
BACKUP_DIR="${SWITCHBOARD_BACKUP_DIR:-$SWITCHBOARD_BASE/model-backups}"
```

**validate.py** and **redundancy.py**:
```python
BASE = Path(os.environ.get("SWITCHBOARD_BASE", Path.home() / ".openclaw"))
CONFIG_PATH = Path(os.environ.get("SWITCHBOARD_CONFIG", BASE / "openclaw.json"))
BACKUP_DIR = Path(os.environ.get("SWITCHBOARD_BACKUP_DIR", BASE / "model-backups"))
```

**server.py**: Already partially done (`SWITCHBOARD_ENV` and `SWITCHBOARD_PORT` exist). Add `SWITCHBOARD_CONFIG` and `SWITCHBOARD_BACKUP_DIR`.

### 1.2 Abstract the Config Format

The current code reads/writes a specific OpenClaw JSON schema. Create a thin adapter layer:

```
config/
  adapter.py       — normalize/denormalize between Switchboard's internal model and any config format
  openclaw.py      — OpenClaw adapter (current behavior)
  generic.py       — Generic adapter: { "primary": "...", "fallbacks": [...] }
```

The generic adapter allows use with any agent framework or standalone. The OpenClaw adapter preserves the current behavior.

### 1.3 Abstract the CLI Dependency

Currently calls `openclaw models set <model>` to apply changes. Create a pluggable apply layer:

```bash
# In switchboard.sh
if command -v openclaw &>/dev/null && [[ -z "$SWITCHBOARD_STANDALONE" ]]; then
  openclaw models set "$model"
else
  # Direct config edit (atomic write, already implemented)
  apply_direct "$model" "$role"
fi
```

In standalone mode (`SWITCHBOARD_STANDALONE=1` or when OpenClaw is absent), apply changes directly to the JSON config. This is already implemented as a fallback — just needs to be the default path when OpenClaw isn't available.

### 1.4 Generic Config Schema

Define a minimal standalone config format (`switchboard.json`) as the default for non-OpenClaw users:

```json
{
  "model": {
    "primary": "anthropic/claude-sonnet-4-6",
    "fallbacks": [
      "openai/gpt-4o",
      "google/gemini-2-pro"
    ],
    "imageModel": {
      "primary": "openai/dall-e-4",
      "fallbacks": []
    }
  },
  "allowlist": []
}
```

---

## Phase 2: Documentation

### 2.1 README Rewrite

The current README is OpenClaw-focused. Rewrite for a standalone audience:

- **What it is**: Model routing + fallback management for AI agent frameworks
- **Why it exists**: Prevent gateway crashes from bad model assignments; single-command rollback; provider diversity enforcement
- **Quick start** (5 minutes to working):
  ```bash
  git clone https://github.com/frank-bot07/model-switchboard
  cd model-switchboard
  ./scripts/setup.sh
  ./scripts/switchboard.sh health
  ```
- **Usage examples**: set-primary, add-fallback, restore, ui
- **Config format** with full schema reference
- **Environment variables** reference table
- **Adapter guide**: how to use with OpenClaw / custom frameworks

### 2.2 API Reference

Auto-generate from switchboard.sh help text. Document every command with:
- Syntax
- Description
- Arguments
- Examples
- Exit codes

Create `docs/CLI.md`.

### 2.3 Architecture Guide

Expand ARCHITECTURE.md into a full contributor guide:
- Decision flow diagram (validation → backup → apply → health check)
- Config schema reference
- Validation engine internals
- Redundancy scoring algorithm
- Adapter pattern for custom frameworks

### 2.4 Provider Setup Guide

Current: setup wizard assumes credentials already exist. Add `docs/PROVIDERS.md`:
- How to get API keys for each supported provider
- Env var names for each provider
- Which models need which env vars
- Testing auth: `./scripts/switchboard.sh validate`

---

## Phase 3: Testing

No automated tests is the biggest quality gap. This is the most important non-decoupling work.

### 3.1 Unit Tests (Python)

`tests/unit/`
- `test_validate.py` — Exercise every validation path in validate.py
  - Valid refs, invalid refs, role mismatches, hard blocks
  - Registry loading (missing file, malformed JSON, empty registry)
  - Config schema validation (all required keys, type errors)
- `test_redundancy.py` — Redundancy engine
  - Provider detection (env vars set/unset)
  - Chain building (diversity enforcement, min depth, scoring)
  - Fail-safe behavior (registry unavailable)

### 3.2 Integration Tests (Bash)

`tests/integration/`
- `test_switchboard.sh` — End-to-end CLI tests
  - set-primary → verify config changed
  - set-primary invalid → verify config unchanged, exit code 1
  - add-fallback → verify chain
  - restore → verify rollback
  - import → verify schema validation rejects bad input
  - backup → verify backup created + pruning at 30

### 3.3 UI Tests

`tests/ui/`
- Manual test checklist (TESTING.md) for the Canvas dashboard
- Optionally: Playwright tests for the dashboard if/when the project matures

### 3.4 Test Fixtures

`tests/fixtures/`
- `openclaw-config.json` — Valid OpenClaw config for tests
- `generic-config.json` — Valid generic config for tests
- `model-registry-small.json` — Minimal registry for fast tests
- `bad-configs/` — Invalid configs that should fail schema validation

---

## Phase 4: Code Quality

### 4.1 Error Messages

Current error messages are functional but terse. For a public product, improve:
- Include the fix hint in every error: "Model 'dall-e-3' is an image model and cannot be used as primary LLM. Use `set-image` instead."
- Distinguish config errors (user's fault) from internal errors (tool bug)

### 4.2 Exit Codes

Document and standardize exit codes across switchboard.sh:
- `0` — success
- `1` — validation error (user input problem)
- `2` — config error (config file problem)
- `3` — system error (missing dependency, permission denied)
- `4` — health check failure (change applied but gateway unhealthy)

### 4.3 Logging

Current: progress messages to stdout, errors mixed in. For production:
- Add `--quiet` flag to suppress non-error output (for scripting)
- Add `--json` output flag for machine-readable results
- Log all operations with timestamps to `~/.switchboard/switchboard.log` (configurable)

### 4.4 Python Cleanup

validate.py and redundancy.py have some rough edges:
- Add `if __name__ == "__main__":` guards everywhere (done in some files, not all)
- Type hints on public functions
- Consistent return value patterns (currently some return dicts, some print and exit)

---

## Phase 5: Packaging & Distribution

### 5.1 Installer Script

Create `install.sh` — one-command install for new users:
```bash
curl -fsSL https://raw.githubusercontent.com/frank-bot07/model-switchboard/main/install.sh | bash
```

What it does:
1. Clone repo to `~/.switchboard/`
2. Add `alias switchboard="~/.switchboard/scripts/switchboard.sh"` to shell profile
3. Run `setup.sh`
4. Print "Done. Run: switchboard health"

### 5.2 Homebrew Formula (Optional, v2)

If project gets traction, a `brew install model-switchboard` would help adoption.

### 5.3 npm Wrapper (Optional, v2)

Many AI developers are in the Node ecosystem. A thin npm package that invokes the Bash CLI would lower the barrier:
```bash
npx model-switchboard set-primary anthropic/claude-opus-4-6
```

---

## Phase 6: UI/UX Improvements

### 6.1 Provider Auth Management

Current: Dashboard shows red/green dots but can't add keys. Add:
- "Add Key" button per provider → opens input modal → writes to .env file
- Test button: validates key is working (makes a minimal API call)
- This is partially implemented in server.py but not wired to UI

### 6.2 Model Registry Updates

Current: model-registry.json is static and ships with the repo. New models are released constantly. Add:
- `switchboard.sh update-registry` — fetches latest registry from GitHub releases
- Or: registry versioning with a hosted latest.json endpoint
- Dashboard shows "Registry last updated: X days ago" warning if stale

### 6.3 Cost Visibility

Current: cost tiers (free, low, medium, high) but no $ figures. Add:
- Approximate cost per 1M tokens for each model in registry
- Dashboard shows estimated cost comparison between current primary and alternatives
- This helps users make informed decisions, not just functional ones

### 6.4 Dark Mode

Dashboard uses a gray palette. Add a dark mode toggle. Saves to localStorage.

### 6.5 Mobile Responsive

Currently desktop-only. Not critical for a CLI tool's UI, but worth noting.

---

## Phase 7: CI/CD

### 7.1 GitHub Actions Workflows

`.github/workflows/`

**test.yml** — Run on every PR:
```yaml
- run: python -m pytest tests/unit/
- run: bash tests/integration/test_switchboard.sh
- run: python scripts/validate.py config tests/fixtures/openclaw-config.json
```

**lint.yml**:
```yaml
- run: shellcheck scripts/switchboard.sh scripts/setup.sh
- run: python -m flake8 scripts/validate.py scripts/redundancy.py scripts/ui/server.py
```

**registry-validate.yml** — Validate model-registry.json on every change:
```yaml
- run: python -c "import json; json.load(open('model-registry.json'))"
- run: python scripts/validate.py config  # Uses registry as part of full validation
```

### 7.2 Release Process

- Semantic versioning (already on v3.0 — continue)
- CHANGELOG.md update required per release (already maintained)
- GitHub Releases with tagged version + install instructions

---

## Phase 8: Security Hardening (Post-Audit Gaps)

The v3.0 Opus audit fixed all HIGH/MEDIUM issues. These LOW items remain:

### 8.1 Automated Test Suite for Security

The audit identified that the lack of tests means regressions could reintroduce fixed vulnerabilities. The Phase 3 test suite should explicitly include:
- Regression tests for H-1 (XSS) — test that UI renders attacker-controlled model names safely
- Regression tests for H-2 (shell injection) — test that import rejects shell metacharacters in model names
- Regression tests for M-5 (schema validation) — test that malformed import files are rejected

### 8.2 Supply Chain

Currently ships with a static model-registry.json. If a future registry-update feature is added:
- Verify registry downloads against a SHA256 checksum
- Serve registry from GitHub Releases (not a mutable URL)
- Never exec code from the registry (data only)

### 8.3 Server.py Binding

server.py binds to `localhost` only (good). Document this explicitly in the README and add a startup warning if someone tries to bind to `0.0.0.0`.

---

## Prioritized Backlog

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | Phase 1: Decouple from OpenClaw | Medium | Required for standalone |
| P0 | Phase 2: README rewrite | Small | Required for public product |
| P1 | Phase 3: Unit + integration tests | Medium | Quality gate |
| P1 | Phase 7: CI/CD (test + lint) | Small | Quality gate |
| P2 | Phase 4: Error messages + exit codes | Small | Polish |
| P2 | Phase 5: install.sh | Small | Distribution |
| P3 | Phase 6: Provider auth UI completion | Medium | Nice to have |
| P3 | Phase 6: Model registry updates | Medium | Nice to have |
| P4 | Phase 6: Cost visibility | Medium | Future |
| P4 | Phase 5: Homebrew/npm | Large | Future |

---

## What's Already Production-Ready (Keep As-Is)

- Validation engine (validate.py) — comprehensive, fail-closed, well-tested manually
- Redundancy engine (redundancy.py) — provider diversity enforcement works
- Atomic write + backup system — battle-tested pattern
- Security posture — all H/M audit findings resolved
- Canvas dashboard — XSS-safe, no external deps, clean UI
- Model registry (model-registry.json) — 50+ models, well-structured
- Zero external dependencies — huge selling point, keep this

---

## Recommended First PR Sequence

1. `chore: add SWITCHBOARD_BASE env var for configurable paths` — unblocks standalone use
2. `feat: standalone mode (direct config edits without openclaw CLI)` — P0 decoupling
3. `docs: rewrite README for standalone audience` — makes it publishable
4. `chore: add install.sh` — one-command install
5. `test: add pytest unit tests for validate.py and redundancy.py` — quality gate
6. `ci: add GitHub Actions test + lint workflows` — CI gate

After these 6 PRs, the project is genuinely standalone and production-ready as an open-source tool.
