# Bloodline Connect

A Flask + SQLAlchemy blood donation management system with donor registration, blood requests, donation tracking, authentication, and admin access control.

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit SECRET_KEY and demo passwords
python backend.py
```

Open <http://127.0.0.1:5000>. The default development database is SQLite (`bloodline.db`). For MySQL, set `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, and `DB_NAME`.

## Demo data

The first run seeds sample records. Set `DEMO_ADMIN_PASSWORD` and `DEMO_DONOR_PASSWORD` before starting the app; do not use the development defaults in a public deployment.

## Deployment note

This repository includes a static project page in `docs/` for GitHub Pages. GitHub Pages serves static files only; it cannot run this Flask backend or its database. Deploy the Flask app to a Python-capable host (for example Render, Railway, Fly.io, or a VPS) for a publicly usable application, while the GitHub Pages site provides project information and setup instructions.
