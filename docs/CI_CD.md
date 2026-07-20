# CI/CD (GitHub Actions)

The workflow file could not be committed automatically because the authoring
token lacks the `workflow` OAuth scope required for files under
`.github/workflows/`. The workflow definition is provided at `docs/ci.yml`.

To activate CI/CD, add it with your own (workflow-scoped) credentials:

```bash
mkdir -p .github/workflows
git mv docs/ci.yml .github/workflows/ci.yml   # or cp
git commit -m "Add CI/CD workflow"
git push
```

The pipeline runs on every push/PR:
1. Install dependencies
2. `ruff check` (lint)
3. `pytest` with coverage (fails under 80%)
4. Build backend & frontend Docker images
5. On `main`: trigger a Render deploy (if `RENDER_DEPLOY_HOOK_URL` secret is set)
