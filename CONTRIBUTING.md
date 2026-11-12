# Contributing

Thanks for helping! Bug reports, ideas and pull requests are welcome.

## Development setup

```bash
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt && pytest
PSADT_COOKIE_SECURE=false uvicorn app.main:app --reload    # http://localhost:8000
cd ../frontend && npm install && npm run dev                # http://localhost:5173
```

For export features locally, download `PSAppDeployToolkit_Template_v4.zip` from the
[PSADT releases](https://github.com/PSAppDeployToolkit/PSAppDeployToolkit/releases) and set `PSADT_TOOLKIT_ZIP`.

## Guidelines

- Keep Docker (`Dockerfile`) and LXC (`lxc/install.sh`) behaviour identical; change both together.
- New step types: add the model in `backend/app/psadt/schema.py`, rendering in `generator.py`, the form in `frontend/src/steps.js`, and a test.
- Never execute user-provided PowerShell on the server.
- `pytest` must pass and `npm run build` must succeed (CI checks both).
- Versioning: bump `VERSION` and `frontend/package.json` by 0.0.11 per release; merging a version bump to `main` creates the GitHub release and Docker image automatically.
