# Contribution and Phase Delivery Workflow

Use this workflow for every project phase and feature. A change is complete only
after local validation, CI, review, and merge; a successful local run alone is
not enough.

## 1. Start from the latest `main`

Run from the repository root:

```powershell
git switch main
git pull --ff-only origin main
git switch -c feature/<phase-or-feature>
```

Use a focused branch name, for example `feature/pdf-ingestion`,
`feature/citation-generation`, or `feature/frontend-ui`. Do not develop phase
work directly on `main`.

## 2. Implement one reviewable change

- Keep the PR focused on one phase or closely related feature.
- Add or update tests and documentation alongside behavior changes.
- Do not commit `.env`, API keys, database credentials, local model files, PDFs,
  database volumes, build output, or virtual environments.
- Keep local-only seed PDFs in `data/raw_pdfs/`; they are intentionally ignored
  by Git. Describe how reviewers can obtain or provide test data instead.

## 3. Run local checks before every push

Backend checks:

```powershell
cd backend
python -m ruff check .
python -m pytest -q
cd ..
```

Frontend checks when `frontend/` is included:

```powershell
cd frontend
npm ci
npm run lint
npm run build
cd ..
```

For database, migration, or Docker changes, also validate against the local
Compose services:

```powershell
docker compose config --quiet
docker compose up -d db
docker compose run --rm backend alembic upgrade head
docker compose build backend
```

Run a manual API/browser smoke test when a change affects runtime behavior.
Never make CI depend on a paid provider or a developer's local data. Unit tests
should mock external model calls; use PostgreSQL service containers for
database-backed checks.

Before staging, review the full change:

```powershell
git status --short
git diff --check
git diff
```

## 4. Stage only the intended files and inspect the exact commit

Prefer explicit paths to `git add -A`, especially when `.env`, PDFs, frontend
experiments, or other unrelated files are present:

```powershell
git add <intended paths>
git diff --cached --check
git diff --cached --stat
git diff --cached
```

Confirm no secret, PDF, generated artifact, or unrelated change is staged.
If a secret was ever committed, removing it in a later commit is not sufficient:
revoke/rotate it immediately.

## 5. Commit and push the feature branch

Use a concise conventional commit message:

```powershell
git commit -m "feat: add PDF ingestion pipeline"
git push -u origin feature/<phase-or-feature>
```

Push follow-up commits to the same feature branch. Each push runs CI.

## 6. Open and maintain the pull request

- Open a PR from the feature branch into `main`; use the repository PR template.
- Keep the PR description current as implementation or test results change.
- Link related issues and explain user-visible behavior, migrations, and risks.
- Wait for all required CI jobs to pass. Fix failures and push the correction;
  do not merge with red or skipped required checks.
- Review the diff and CI results on GitHub. Resolve reviewer feedback with
  follow-up commits and reply when each item is addressed.
- Keep the PR focused; split unrelated work rather than expanding its scope.
- Merge only after checks pass and required review/approval is complete. Use
  squash merge for the feature branch unless the repository maintainers choose
  another merge strategy.

## 7. Tag completed milestones

After a phase PR is merged and the milestone is verified on `main`, create and
push an annotated phase tag using the versioning convention agreed for the
repository, for example:

```powershell
git switch main
git pull --ff-only origin main
git tag -a v0.3.0-ingestion -m "Phase 3: PDF ingestion pipeline"
git push origin v0.3.0-ingestion
```

Do not tag an unmerged feature branch or a milestone whose CI is failing.

## CI/CD expectations

`.github/workflows/ci.yml` runs on pushes to any branch or version tag, and on
PRs targeting `main`. It checks Python 3.11 and 3.12, runs Ruff, applies Alembic
migrations against PostgreSQL with pgvector, runs backend tests, lints/builds
the frontend, and builds the backend Docker image. Only a successful push to
`main` publishes the image to GHCR.

To prevent merging around CI, repository administrators should configure
GitHub Rulesets or branch protection for `main`:

1. Require pull requests before merging.
2. Require the Backend checks for Python 3.11 and 3.12, Frontend — Lint and
   Build, and Backend — Docker Build status checks.
3. Require approval if another reviewer is available; otherwise document the
   solo-maintainer exception in the PR.
4. Require conversations to be resolved and disallow force pushes/deletion of
   `main`.

The tag push runs CI and, if every check passes, publishes a version-tagged
image to GHCR. A push to `main` publishes the `latest` image. The workflow file
runs checks, but branch protection is a GitHub repository setting and cannot be
enabled by changing this repository's source files.
