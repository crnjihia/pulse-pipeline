# Release Strategy & Pipeline Versioning

Pulse Pipeline follows strict **Semantic Versioning (SemVer 2.0.0)**: `MAJOR.MINOR.PATCH`.

---

## 1. Release Cadence

* **Major (`X.0.0`)**: Incompatible API changes, major schema overhauls, or breaking database migrations.
* **Minor (`0.X.0`)**: New datasets added (e.g., adding Treasury Bills or Port Telemetry), new transformation rules, or dashboard enhancements.
* **Patch (`0.0.X`)**: Bug fixes, schema typing corrections, resilience improvements, or documentation updates.

---

## 2. Automated Release Workflow

Releases are automated via GitHub Actions (`.github/workflows/release.yml`):

1. **Tag Trigger**: A Git tag matching `v*.*.*` (e.g. `v0.1.0`) is pushed to GitHub.
2. **Quality Verification**: Full CI suite (Ruff linter, Mypy type checker, and Pytest coverage suite) must pass.
3. **Artifact Generation**: Python source distribution (`sdist`) and binary wheel (`.whl`) are built using `python -m build`.
4. **Checksum Verification**: SHA256 checksums are calculated and packaged as `checksums.txt`.
5. **GitHub Release Publication**: GitHub Release is automatically published with release notes, changelog summary, and attached wheel/sdist assets.
6. **Docker Package Build**: The GHCR Docker container workflow tags and publishes corresponding version tags (`ghcr.io/crnjihia/pulse-pipeline:0.1.0`).

---

## 3. Creating a New Version Release

Developers can release either by pushing a tag or using GitHub Actions `workflow_dispatch`:

```bash
# Tag a new release
git tag -a v0.1.0 -m "Release v0.1.0: Initial production release"
git push origin v0.1.0
```
