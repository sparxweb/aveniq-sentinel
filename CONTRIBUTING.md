# Contributing to Aveniq Sentinel

Thank you for contributing to **Aveniq Sentinel** by **Aveniq**! We welcome contributions that advance our network intrusion detection analytics, data engineering pipelines, exploratory data analysis, and machine learning architectures.

Official Repository: [https://github.com/sparxweb/aveniq-sentinel](https://github.com/sparxweb/aveniq-sentinel)

---

## 1. Code of Conduct & Core Principles

Aveniq Sentinel is engineered as an enterprise-grade cybersecurity analytics platform. All contributions must adhere to these foundational principles:

1. **Scientific Integrity & No Data Leakage:**
   - Raw flow identifiers (`Flow ID`, `Source IP`, `Destination IP`, `Timestamp`) must never enter modeling feature sets.
   - Exact duplicate flow records must be deduplicated prior to cross-validation partitioning.
   - Non-parametric rate features (`Flow Bytes/s`, `Flow Packets/s`) must be sanitized of division-by-zero infinities.
2. **Strict Dependency Governance:**
   - Zero new external libraries or remote dependencies may be added without prior architectural review. All features must operate within the approved local environment (`pandas`, `numpy`, `scikit-learn`, `pyarrow`, `streamlit`, `plotly`, `pytest`, `networkx`).
3. **Immutable Raw Data:**
   - Raw dataset files in `data/raw/` must remain strictly read-only and immutable.
4. **Reproducible Engineering:**
   - All analytics, metrics, and figures must originate from measured data, never hardcoded mock values.

---

## 2. Git Branching Strategy

We follow a structured branching workflow to ensure stability:

| Branch Type | Naming Convention | Description | Example |
|---|---|---|---|
| **Production** | `main` | Production-ready, verified codebase. | `main` |
| **Development** | `develop` | Integration branch for upcoming phases. | `develop` |
| **Feature** | `feature/<short-desc>` | New capabilities or data engineering modules. | `feature/packet-symmetry-ratio` |
| **Bug Fix** | `bugfix/<issue-id>` | Corrections to verified defects or calculations. | `bugfix/fix-plotly-axes` |
| **Testing** | `test/<name>` | New unit tests, integration tests, or benchmarks. | `test/add-chart-coverage` |
| **Documentation** | `docs/<name>` | Updates to guides, reports, or data dictionaries. | `docs/phase2-audit-update` |

### Step-by-Step Feature Branching Workflow

```powershell
# 1. Fetch latest changes and switch to main
git checkout main
git pull origin main

# 2. Create and switch to your feature branch
git checkout -b feature/lossless-downcasting-enhancement

# 3. Make changes and verify tests locally
pytest tests/ -v

# 4. Commit using Conventional Commit standards
git commit -m "feat(loader): optimize numeric downcasting memory reduction"

# 5. Push branch and open a Pull Request
git push origin feature/lossless-downcasting-enhancement
```

---

## 3. Commit Message Standards

We enforce [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

[optional body explaining motivation and technical decisions]
```

### Commit Types:
- `feat`: A new feature or analytical capability.
- `fix`: A bug fix or calculation error correction.
- `refactor`: Code restructuring without behavioral change.
- `test`: Adding or updating test suites.
- `docs`: Documentation updates or additions.
- `perf`: Memory reduction or runtime optimizations.
- `chore`: Configuration, formatting, or project housekeeping.

### Examples:
- `feat(features): implement directional packet symmetry ratio`
- `fix(cleaning): resolve division-by-zero infinity in rate calculations`
- `test(validation): add edge case tests for empty DataFrames`
- `docs(readme): add executive architecture diagram and quickstart guide`

---

## 4. Local Testing & Verification

Before submitting any Pull Request, ensure that all automated unit tests pass locally:

```powershell
# Run the entire test suite
pytest tests/ -v

# Run tests with short traceback
pytest tests/ -q --tb=short

# Verify application entrypoints
python -c "import app; import streamlit_app; from neuralshield import dashboard; print('Entrypoints OK!')"
```

All 54+ tests must pass with zero errors.

---

## 5. Pull Request Standards

When opening a Pull Request:
1. Use the provided [PR Template](.github/pull_request_template.md).
2. Clearly explain what changes were made and why.
3. Confirm that no target leakage was introduced.
4. Verify that the Streamlit dashboard launches and renders cleanly via `python -m streamlit run app.py`.
