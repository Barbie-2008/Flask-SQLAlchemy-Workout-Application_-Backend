# Workout Tracker API

A Flask and SQLAlchemy REST API for tracking exercises, workouts, and the
exercises assigned to each workout.

## Requirements

- Python 3.12
- Pipenv

## Install

From the repository root:

```bash
pipenv install --dev
```

## Initialize the database

The SQLite database is stored at `server/instance/app.db`. This project
currently uses SQLAlchemy `create_all()` rather than Alembic migrations.

To create an empty database, run this from the repository root:

```bash
PYTHONPATH=server pipenv run python - <<'PY'
from app import app
from models import db

with app.app_context():
    db.create_all()
PY
```

To create the schema and load the sample workouts and exercises instead:

```bash
pipenv run python server/seed.py
```

**Warning:** the seed script clears existing workouts, exercises, and their
associations before inserting the sample data. Do not run it if you need to
preserve data in the local database.

## Run the API

From the repository root:

```bash
pipenv run python server/app.py
```

The development server listens at `http://127.0.0.1:5555`. It runs with Flask
debug mode enabled and is intended for local development, not production.

## API

All request bodies should be JSON. IDs in route paths are integers.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | API welcome message |
| `GET` | `/exercises` | List exercises |
| `GET` | `/exercises/<exercise_id>` | Get an exercise and its workouts |
| `POST` | `/exercises` | Create an exercise |
| `DELETE` | `/exercises/<exercise_id>` | Delete an exercise |
| `GET` | `/workouts` | List workouts |
| `GET` | `/workouts/<workout_id>` | Get a workout and its exercises |
| `POST` | `/workouts` | Create a workout |
| `DELETE` | `/workouts/<workout_id>` | Delete a workout |
| `POST` | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout |

### Create an exercise

```json
{
  "name": "Push-ups",
  "category": "Strength",
  "equipment_needed": false
}
```

`name` and `category` are required. `equipment_needed` defaults to `false`.
Supported categories are `Strength`, `Cardio`, `Flexibility`, `Balance`, and
`Hiit`.

### Create a workout

```json
{
  "date": "2026-10-22",
  "duration_minutes": 45,
  "notes": "Upper body"
}
```

`date` must use `YYYY-MM-DD` format. `duration_minutes` must be a positive
integer. `notes` is optional and may be `null`.

### Add an exercise to a workout

Send any of `reps`, `sets`, and `duration_seconds`; each is optional and must
be a non-negative integer when provided. For example:

```json
{
  "reps": 12,
  "sets": 3
}
```

Create the exercise and workout first. The API returns `404` if either ID does
not exist.

Successful creates return `201`, successful reads return `200`, and successful
deletes return `204` with an empty response body. Validation errors return
`400` with an `errors` object; missing resources return `404`.

## Run tests

From the repository root:

```bash
pipenv run pytest 
```
