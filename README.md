# TaskFlow API

[![CI](https://github.com/manishtiwari2/taskflow-api/actions/workflows/ci.yml/badge.svg)](https://github.com/manishtiwari2/taskflow-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Django](https://img.shields.io/badge/django-5.2%20LTS-092E20)
![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)

A REST API for managing projects and tasks. Users create projects, invite members and assign tasks. Built with Django REST Framework and PostgreSQL, tested, containerised and checked by CI on every pull request.

## Highlights
- **JWT authentication.** Register, log in and refresh tokens with `simplejwt`. Custom `User` model with unique email.
- **Owner/member permissions.** Data is scoped in the queryset: non-members get `404`, members who are not the owner get `403` on changes.
- **Business rules in the serializer.** A task can only be assigned to a project member. Removing a member unassigns their tasks.
- **Filtering, search, ordering, pagination.** `?status=done&priority=high&search=docs&ordering=-due_date`, 20 items per page.
- **No N+1 queries.** Project lists use `prefetch_related`. A test caps the query count at 3.
- **Throttling.** 30 requests/min for anonymous users, 300/min for logged-in users.
- **Live API docs.** OpenAPI schema and Swagger UI with `drf-spectacular`.
- **Quality gates.** 46 tests, 99% coverage, `ruff` lint and format, migration check, GitHub Actions on PostgreSQL 16.

## Tech stack
| Area | Tools |
|---|---|
| Framework | Python 3.12+, Django 5.2 LTS, Django REST Framework |
| Database | PostgreSQL 16 (Docker Compose) |
| Auth | `djangorestframework-simplejwt` |
| API features | `django-filter`, `drf-spectacular`, `django-cors-headers` |
| Config | `django-environ` (`.env`, nothing secret in git) |
| Quality | `pytest`, `pytest-django`, `pytest-cov`, `ruff` |
| CI | GitHub Actions with a PostgreSQL service container |

## Try it in 2 minutes
Needs Python 3.12+, Docker Desktop and Git.

```bash
git clone https://github.com/manishtiwari2/taskflow-api.git
cd taskflow-api
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash. Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
docker compose up -d
python manage.py migrate
python manage.py runserver
```

- Health check: http://127.0.0.1:8000/api/health/ returns `{"status":"ok","database":"ok"}`.
- Swagger UI: http://127.0.0.1:8000/api/docs/

## Example
```bash
curl -X POST localhost:8000/api/v1/auth/register/ -H "Content-Type: application/json" \
  -d '{"username":"ann","email":"ann@example.com","password":"StrongPass123!"}'
curl -X POST localhost:8000/api/v1/auth/token/ -H "Content-Type: application/json" \
  -d '{"username":"ann","password":"StrongPass123!"}'
curl -X POST localhost:8000/api/v1/projects/ -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" -d '{"name":"Website"}'
```

## API reference
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

**Task list options:** `?status=`, `?priority=`, `?assignee=`, `?project=`, `?search=` (title, description), `?ordering=created_at|due_date|status` (prefix `-` to reverse), `?page=`.

## Tests and checks
```bash
pytest --cov
ruff check .
ruff format --check .
```
Tests cover auth, CRUD, permissions, filters, query count, API docs and throttling. CI runs the same checks plus `python manage.py makemigrations --check --dry-run`.

## Project structure
```
config/    settings, root urls
accounts/  custom User, register, me
projects/  Project model, viewset, owner permission
tasks/     Task model, serializer, viewset, filters
core/      health check
tests/     pytest tests and shared fixtures
docs/      INTERVIEW_NOTES.md (design walkthrough and Q&A)
```
Request flow: router -> throttle -> JWT authentication -> permission -> viewset (scoped queryset) -> serializer (validation) -> database.

## Design decisions
- **Custom User from day one.** Changing `AUTH_USER_MODEL` after the first migration is painful.
- **Scoped querysets, 404 for non-members.** Other users' objects look like they do not exist.
- **Owner counts as a member.** `Project.objects.for_user()` returns projects where I am owner or member, in one place.
- **Assignee must be a member.** Checked in the task serializer.
- **Config from the environment.** Secrets never go in git.

## Possible next steps
Refresh-token blacklist on logout, Redis-backed throttling, task comments and history, soft delete, a Dockerfile for the app itself.
