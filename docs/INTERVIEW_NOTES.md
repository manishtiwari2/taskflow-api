# Interview notes: TaskFlow API

One-line pitch: "A REST API for projects and tasks, built with Django REST Framework and PostgreSQL. It has JWT login, owner/member permissions, filtering, tests, Docker and CI."

## What each part does, and why I chose it

| Part | What it does | Why |
|---|---|---|
| `config/` | Settings and root URLs. Settings come from `.env`. | Secrets stay out of git. Same code runs locally and in CI. |
| `accounts/` | Custom `User` (unique email), register, `me`, JWT login. | A custom user from day one avoids a painful change later. |
| `projects/` | `Project` model, CRUD, add/remove members, owner permission. | The owner controls the project; members can read it. |
| `tasks/` | `Task` model, CRUD, filters, search, ordering. | Members work on tasks inside their projects. |
| `core/` | `/api/health/` checks the app and the database. | Monitors and Docker can ask "are you alive?". |
| PostgreSQL 16 (Docker) | The database. | Real database for dev and tests, same as production. |
| `simplejwt` | Access and refresh tokens. | Stateless login. A React app can send the token in a header. |
| `django-filter` | `?status=done&priority=high`. | Standard, tested filtering. |
| `drf-spectacular` | OpenAPI schema and Swagger UI at `/api/docs/`. | Docs that match the code. The frontend can use them. |
| `pytest` + `ruff` | Tests, lint, format. | Fast tests and one tool for style. |
| GitHub Actions | Runs checks on every PR. | Bad code cannot be merged by mistake. |

## Request flow
1. A request comes to `/api/v1/tasks/`.
2. Django routes it to `TaskViewSet`.
3. **Throttle** checks the rate limit (30/min anonymous, 300/min logged in).
4. **JWT authentication** reads the `Authorization: Bearer` header and finds the user.
5. **Permission** checks (`IsAuthenticated`, and `IsOwnerOrReadOnly` for projects).
6. `get_queryset()` returns only the user's data.
7. The **serializer** validates input (for example, the assignee must be a member).
8. The ORM talks to PostgreSQL. The serializer builds the JSON response.

## How permissions work
- Every queryset is scoped: `Project.objects.for_user(user)` returns projects where I am the owner or a member. Tasks are filtered by that same set of projects.
- **Not a member** -> the object is not in my queryset -> **404**. The API does not reveal that it exists.
- **Member, not owner** -> I can read the project, but update, delete and member changes give **403** (`IsOwnerOrReadOnly`).
- **Any member** can create, update and delete tasks in the project.
- Creating a task in someone else's project returns 400 "Invalid pk", the same as an unknown id. Filtering by `?project=` is limited to my projects for the same reason.

## How N+1 was fixed
- N+1 means: 1 query for the list, then 1 more query for each row. 10 projects -> 11+ queries.
- `GET /projects/` shows each project's `members`. That is a many-to-many field, so Django asked for members once per project.
- Fix: `prefetch_related("members")`. Django loads all members in one extra query. Now the list takes 3 queries (count, projects, members) however many projects exist.
- Proof: `tests/test_query_count.py` uses `django_assert_max_num_queries(3)`. I checked that the test fails when I remove the fix.
- Tasks do not need `select_related`: the serializer only returns ids (`project`, `assignee`), and DRF reads those from the row without a new query.

## What CI does (`.github/workflows/ci.yml`)
On every pull request and push to `main`:
1. Starts a PostgreSQL 16 service container.
2. Installs `requirements-dev.txt` (pinned versions).
3. `ruff check` and `ruff format --check` (style).
4. `makemigrations --check --dry-run` (fails if I changed a model but forgot the migration).
5. `pytest --cov` (all tests, with coverage).

## 10 likely questions

1. **Why a custom User model?**
   Django's docs recommend it. After the first migration it is very hard to switch. Mine adds a unique email and can grow later.

2. **Why JWT and not sessions?**
   The API is for a separate frontend (React). A token in a header works without cookies or CSRF. The access token is short-lived; the refresh token gets a new one.

3. **How do you stop users seeing other users' data?**
   Scoped querysets. Each viewset only queries rows for the current user, so there is no object to leak. Tests cover this.

4. **Why 404 and not 403 for non-members?**
   403 says "it exists, but you can't see it". 404 hides that. Members who are not the owner get 403, because they already know the project exists.

5. **What is the N+1 problem?**
   One query for a list plus one query per row for related data. I fixed it with `prefetch_related` and added a test that counts queries.

6. **`select_related` vs `prefetch_related`?**
   `select_related` uses a SQL JOIN for foreign keys and one-to-one. `prefetch_related` runs a second query and joins in Python; it is used for many-to-many and reverse relations (like `members`).

7. **How do you check that an assignee is a project member?**
   In `TaskSerializer.validate()`. It uses `Project.is_member()`. The owner counts as a member. If a member is removed, their tasks become unassigned.

8. **How do filtering, search and pagination work?**
   Global DRF settings add `DjangoFilterBackend`, `SearchFilter` and `OrderingFilter`, and page-number pagination (20 per page). `TaskFilter` defines the filters. The `project` filter only offers my projects.

9. **What does `makemigrations --check` do in CI?**
   It fails if models changed without a new migration file. It stops "works on my machine" database bugs.

10. **What would you improve next?**
    Blacklist refresh tokens on logout, run the app in Docker too, use Redis for throttling when there are many servers, add comments and activity history on tasks, and add soft delete.
