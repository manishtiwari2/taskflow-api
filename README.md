# taskflow-api

REST API for projects and tasks: Django REST Framework, PostgreSQL, JWT auth, Docker, GitHub Actions CI.

## Stack
Django 5.2 LTS, Django REST Framework, PostgreSQL 16 (Docker), pytest, ruff.

## Local setup
Needs Python 3.12+, Docker Desktop and Git.

1. Clone and enter the repo:
   ```bash
   git clone https://github.com/manishtiwari2/taskflow-api.git
   cd taskflow-api
   ```
2. Create a virtual environment and install packages:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate   # Windows Git Bash. On Linux/macOS: source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```
3. Create your env file (edit `SECRET_KEY` if you like):
   ```bash
   cp .env.example .env
   ```
4. Start PostgreSQL, run migrations, start the server:
   ```bash
   docker compose up -d
   python manage.py migrate
   python manage.py runserver
   ```
5. Check it works: open http://127.0.0.1:8000/api/health/. It should show `{"status":"ok","database":"ok"}`.

## Checks
```bash
ruff check .
ruff format --check .
pytest --cov
```

CI runs the same checks, plus `python manage.py makemigrations --check --dry-run`, on every pull request.
