# Travel Planner API

A RESTful API for managing travel projects and places to visit, built with **FastAPI**, **SQLAlchemy**, and **SQLite**. Places are artworks sourced from the [Art Institute of Chicago public API](https://api.artic.edu/docs/).

---

## Tech Stack

| Layer | Library |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (file: `travel_planner.db`) |
| HTTP Client | httpx (async) |
| Validation | Pydantic v2 |
| Server | Uvicorn |

---

## Project Structure

```
travel_planner/
├── main.py                        # App entry point, router registration
├── requirements.txt
├── travel_planner.db              # Auto-created on first run
└── app/
    ├── database.py                # SQLAlchemy engine & session
    ├── models/
    │   └── models.py              # ORM models: Project, ProjectPlace
    ├── schemas/
    │   └── schemas.py             # Pydantic request/response schemas
    ├── routers/
    │   ├── projects.py            # /api/v1/projects endpoints
    │   └── places.py              # /api/v1/projects/{id}/places endpoints
    └── services/
        ├── artic_service.py       # Art Institute of Chicago API client
        └── project_service.py     # Business logic (CRUD, validation)
```

---

## Setup & Run

### 1. Prerequisites

- Python 3.11+

### 2. Clone / enter the project directory

```bash
cd travel_planner
```

### 3. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the server

```bash
uvicorn main:app --reload
```

The API will be available at **http://localhost:8000**.  
The SQLite database (`travel_planner.db`) is created automatically on first run.

For API endpoints under `/api/v1`, basic authentication is enabled. Use the environment variables `BASIC_AUTH_USERNAME` and `BASIC_AUTH_PASSWORD` to configure credentials (Docker defaults are `admin` / `changeme`).

---

## Interactive Documentation

FastAPI generates interactive docs automatically:

| UI | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

---

### Projects

#### `GET /projects/` — List all projects
```bash
curl http://localhost:8000/api/v1/projects/
```

#### `POST /projects/` — Create a project
```bash
# Minimal
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Chicago Art Tour"}'

# With places pre-loaded (IDs from the Art Institute of Chicago API)
curl -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Chicago Art Tour",
    "description": "Impressionism highlights",
    "start_date": "2025-09-01",
    "places": [
      {"external_id": 27992},
      {"external_id": 14655}
    ]
  }'
```

#### `GET /projects/{id}` — Get a single project
```bash
curl http://localhost:8000/api/v1/projects/1
```

#### `PATCH /projects/{id}` — Update project info
```bash
curl -X PATCH http://localhost:8000/api/v1/projects/1 \
  -H "Content-Type: application/json" \
  -d '{"name": "Renamed Trip", "start_date": "2025-10-10"}'
```

#### `DELETE /projects/{id}` — Delete a project
```bash
curl -X DELETE http://localhost:8000/api/v1/projects/1
# Returns 204 on success
# Returns 409 if any places in the project are already visited
```

---

### Places

#### `GET /projects/{id}/places/` — List places in a project
```bash
curl http://localhost:8000/api/v1/projects/1/places/
```

#### `POST /projects/{id}/places/` — Add a place to a project
```bash
curl -X POST http://localhost:8000/api/v1/projects/1/places/ \
  -H "Content-Type: application/json" \
  -d '{"external_id": 27992}'
```

#### `GET /projects/{id}/places/{place_id}` — Get a single place
```bash
curl http://localhost:8000/api/v1/projects/1/places/1
```

#### `PATCH /projects/{id}/places/{place_id}` — Update notes / mark as visited
```bash
# Add notes
curl -X PATCH http://localhost:8000/api/v1/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{"notes": "Must see the pointillist technique up close!"}'

# Mark as visited
curl -X PATCH http://localhost:8000/api/v1/projects/1/places/1 \
  -H "Content-Type: application/json" \
  -d '{"is_visited": true}'
```

---

## Finding Artwork IDs

Use the Art Institute of Chicago search endpoint to discover IDs:

```bash
# Search by keyword
curl "https://api.artic.edu/api/v1/artworks/search?q=monet&limit=5&fields=id,title,artist_display"

# Fetch a specific artwork
curl "https://api.artic.edu/api/v1/artworks/27992?fields=id,title,artist_display"
```

Some well-known artwork IDs for testing:

| ID | Title | Artist |
|---|---|---|
| 27992 | A Sunday on La Grande Jatte | Georges Seurat |
| 14655 | The Bath | Mary Cassatt |
| 16487 | Nighthawks | Edward Hopper |
| 111628 | Water Lilies | Claude Monet |
| 20684 | American Gothic | Grant Wood |

---

## Business Rules

| Rule | Behaviour |
|---|---|
| Max places per project | 10 — enforced at creation and when adding |
| Duplicate place | A same `external_id` cannot be added to the same project twice (HTTP 409) |
| External validation | Every `external_id` is verified against the Art Institute API before storing |
| Delete protection | A project with any visited place cannot be deleted (HTTP 409) |
| Auto-completion | When **all** places in a project are marked as `is_visited: true`, `is_completed` is set to `true` automatically |

---

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | Deleted (no content) |
| 404 | Project or place not found |
| 409 | Conflict (duplicate place, or delete blocked by visited places) |
| 422 | Validation error (bad input, exceeds limit, artwork not found in API) |
| 503 | Art Institute of Chicago API unreachable |

---

## Running Tests (Manual Walkthrough)

```bash
# 1. Create a project
PROJECT=$(curl -s -X POST http://localhost:8000/api/v1/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Trip"}')
echo $PROJECT
PROJECT_ID=$(echo $PROJECT | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# 2. Add a place
curl -s -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/places/ \
  -H "Content-Type: application/json" \
  -d '{"external_id": 27992}'

# 3. Mark it visited
curl -s -X PATCH http://localhost:8000/api/v1/projects/$PROJECT_ID/places/1 \
  -H "Content-Type: application/json" \
  -d '{"is_visited": true}'

# 4. Verify project is now completed
curl -s http://localhost:8000/api/v1/projects/$PROJECT_ID | python3 -m json.tool

# 5. Attempt to delete a project with a visited place (should return 409)
curl -s -X DELETE http://localhost:8000/api/v1/projects/$PROJECT_ID
```