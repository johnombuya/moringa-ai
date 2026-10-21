# AfyaPlus Platform - Engineering & Contribution Guide

This document establishes the official software engineering standards, branching strategy, versioning policy, and quality gates for the AfyaPlus AI Service Platform.

---

## 1. Branching & Release Strategy

AfyaPlus employs a strict **GitFlow-inspired branching strategy** designed for high reliability in clinical and logistics environments:

```
  main (Production Releases, SemVer tagged vX.Y.Z)
   │
   ├── develop (Integration & Staging)
   │    │
   │    ├── feat/week6-service-platform (Feature branches)
   │    ├── feat/reorder-threshold-tuning
   │    └── fix/auth-token-expiry
   │
   └── hotfix/critical-security-patch (Direct production patches)
```

### Branch Classifications

1. **`main`**:
   - Represents production-ready, deployed software.
   - Protected branch: direct pushes are forbidden.
   - All commits must originate from merged pull requests that passed automated CI.
   - Every merge into `main` must be tagged with a semantic release tag (`vX.Y.Z`).

2. **`develop`**:
   - Integration branch for completed feature development.
   - Staging environment deploys automatically from `develop`.

3. **`feat/<feature-name>`**:
   - Short-lived feature branches cut from `develop`.
   - Examples: `feat/mcp-logistics-server`, `feat/jwt-rbac-guard`.

4. **`fix/<bug-name>`**:
   - Bug fix branches addressing issues found during QA.

5. **`hotfix/<patch-name>`**:
   - Emergency fixes branched directly from `main`, merged back into both `main` and `develop`.

---

## 2. Semantic Versioning Policy (SemVer 2.0.0)

All platform components, Docker images, and git releases adhere strictly to [Semantic Versioning 2.0.0](https://semver.org/):

$$\text{Version Format: } \mathbf{MAJOR.MINOR.PATCH}$$

- **`MAJOR` (e.g., 2.0.0)**: Incompatible API contract changes, breaking Pydantic schema modifications, or auth protocol rewrites.
- **`MINOR` (e.g., 1.1.0)**: Backwards-compatible additions, such as new MCP tools (`reorder_supplies`), new read-only resources, or additional role levels.
- **`PATCH` (e.g., 1.0.1)**: Backwards-compatible bug fixes, performance optimizations, or internal dependency updates.

### Container Tag Alignment
The container image tag built by Docker **must match the Git semantic tag exactly**:
- Git Tag: `v1.0.0` $\rightarrow$ Docker Tag: `afyaplus-platform:1.0.0`
- Git Tag: `v1.1.0` $\rightarrow$ Docker Tag: `afyaplus-platform:1.1.0`

---

## 3. Commit Message Conventions (Conventional Commits)

All commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

$$\text{Format: } \langle\text{type}\rangle(\langle\text{scope}\rangle)\text{: }\langle\text{description}\rangle$$

### Approved Types
- `feat`: A new user-facing or API capability (e.g. `feat(agent): integrate MCP delivery route tool`)
- `fix`: A bug fix (e.g. `fix(auth): handle expired token signature exception`)
- `test`: Adding or updating test suites (e.g. `test(mcp): add deliberate invalid parameter tests`)
- `docs`: Documentation updates (e.g. `docs(report): compile observability trace reconstruction`)
- `chore`: Maintenance tasks, dependencies, or configuration (e.g. `chore(docker): optimize layer cache in Dockerfile`)

---

## 4. Pull Request & Quality Gate Requirements

Before any pull request can be merged into `develop` or `main`, the following automated quality checks must pass:

1. **Automated Unit & Integration Tests**:
   ```bash
   pytest -v tests/
   ```
   All tests must pass (100% pass rate).
2. **Schema & Input Validation**:
   - All Pydantic request models must declare strict field bounds and forbid unexpected extra fields (`model_config = {"extra": "forbid"}`).
3. **Observability Verification**:
   - Every new route or tool must log a single structured log line correlating with the request `trace_id`.
4. **Security & Secrets Hygiene**:
   - Secrets must NEVER be committed to Git or baked into Docker layers.
   - All runtime secrets must be injected via environment variables (`.env` or Kubernetes Secrets).
