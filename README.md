# taskflow-api

REST API for projects and tasks: Django REST Framework, PostgreSQL, JWT auth, Docker, GitHub Actions CI.

## Stack
Django 5.2 LTS, Django REST Framework, PostgreSQL 16 (Docker), JWT (`simplejwt`), `django-filter`, `drf-spectacular` (OpenAPI), pytest, ruff, GitHub Actions.

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

## API reference
Interactive docs: http://127.0.0.1:8000/api/docs/ (Swagger UI). Raw schema: `/api/schema/`.

| Method | Path | Who | What |
|---|---|---|---|
| GET | `/api/health/` | anyone | status and database check |
| POST | `/api/v1/auth/register/` | anyone | create a user |
| POST | `/api/v1/auth/token/` | anyone | get access and refresh tokens |
| POST | `/api/v1/auth/token/refresh/` | anyone | get a new access token |
| GET | `/api/v1/auth/me/` | logged in | current user |
| CRUD | `/api/v1/projects/` | logged in | projects where I am owner or member |
| POST, DELETE | `/api/v1/projects/{id}/members/` | owner | add or remove a member (`{"user_id": 2}`) |
| CRUD | `/api/v1/tasks/` | project members | tasks from my projects |

Send the token as `Authorization: Bearer <access>`.

**Task list options:** `?status=`, `?priority=`, `?assignee=`, `?project=`, `?search=` (title, description), `?ordering=created_at|due_date|status` (prefix `-` to reverse), `?page=`. Lists are paginated, 20 per page.

**Quick try (curl):**
```bash
curl -X POST localhost:8000/api/v1/auth/register/ -H "Content-Type: application/json" \
  -d '{"username":"ann","email":"ann@example.com","password":"StrongPass123!"}'
curl -X POST localhost:8000/api/v1/auth/token/ -H "Content-Type: application/json" \
  -d '{"username":"ann","password":"StrongPass123!"}'
curl -X POST localhost:8000/api/v1/projects/ -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" -d '{"name":"Website"}'
```

## Architecture
```
config/    settings, root urls
accounts/  custom User, register, me
projects/  Project model, viewset, owner permission
tasks/     Task model, serializer, viewset, filters
core/      health check
tests/     pytest tests and shared fixtures
```
Request flow: URL router -> throttle -> JWT authentication -> permission -> viewset (scoped queryset) -> serializer (validation) -> database.

## Design decisions
- **Custom User from day one.** Changing `AUTH_USER_MODEL` after the first migration is painful.
- **Scoped querysets, 404 for non-members.** Each viewset only queries the user's own data, so other users' objects look like they do not exist.
- **Owner is a member.** `Project.objects.for_user()` returns projects where I am owner or member, in one place.
- **Assignee must be a member.** Checked in the task serializer. Removing a member unassigns their tasks.
- **No N+1.** Project lists prefetch members; a test caps the query count.
- **Config from the environment.** `django-environ` reads `.env`; secrets never go in git.
- **Throttling.** 30 requests/min for anonymous users, 300/min for logged-in users.
