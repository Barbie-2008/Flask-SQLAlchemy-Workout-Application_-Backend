# Workout Tracker API

## Project description

Workout Tracker is a REST API built with Flask and SQLAlchemy. It lets clients
create and browse exercises and workouts, and associate exercises with
workouts, including reps, sets, and duration details. The application uses
SQLite for local data storage.

## Installation

### Requirements

- Python 3.12
- Pipenv

From the repository root, install the dependencies:

```bash
pipenv install --dev
```

### Migrate and seed the database

The SQLite database is stored at `server/instance/app.db`. Apply the database
migrations from the `server` directory:

```bash
cd server
pipenv run flask --app app db upgrade
cd ..
```

Seed example exercises, workouts, and workout-exercise associations from the
`server` directory:

```bash
cd server
pipenv run python seed.py
```

**Warning:** the seed script clears all existing workouts, exercises, and
workout associations before inserting sample data. Do not run it if you need
to preserve records in the local database.

## Run instructions

From the repository root, start the Flask development server:

```bash
cd server
pipenv run flask --app app run --port 5555
```

The API is available at `http://127.0.0.1:5555`. The development server is
intended for local development, not production.

## API endpoints

All request bodies must be JSON objects, and IDs in route paths are integers.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Return the API welcome message. |
| `GET` | `/static/<path:filename>` | Flask's default route for serving static files. |
| `GET` | `/exercises` | Return all exercises. |
| `GET` | `/exercises/<exercise_id>` | Return one exercise and its associated workouts. |
| `POST` | `/exercises` | Create an exercise. Requires `name` and `category`; `equipment_needed` defaults to `false`. |
| `DELETE` | `/exercises/<exercise_id>` | Delete an exercise. |
| `GET` | `/workouts` | Return all workouts. |
| `GET` | `/workouts/<workout_id>` | Return one workout and its exercises. |
| `POST` | `/workouts` | Create a workout. Requires a `YYYY-MM-DD` date and positive integer `duration_minutes`; `notes` is optional. |
| `DELETE` | `/workouts/<workout_id>` | Delete a workout. |
| `POST` | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout. Optional `reps`, `sets`, and `duration_seconds` must be non-negative integers or `null`. |

Exercise categories are `Strength`, `Cardio`, `Flexibility`, `Balance`, and
`Hiit`. Create the exercise and workout before associating them. Successful
creates return `201`, reads return `200`, and deletes return `204`. Invalid
input returns `400`; requests for missing resources return `404`.

### Try the API with `curl`

Start the Flask server as described above, then run these commands in a second
terminal. They list exercises and workouts, then show one exercise with its
associated workouts and exercise details. Replace `1` with an ID returned by
your API if needed.

```bash
curl -s http://127.0.0.1:5555/exercises | python -m json.tool
curl -s http://127.0.0.1:5555/workouts | python -m json.tool
curl -s http://127.0.0.1:5555/exercises/1 | python -m json.tool
```

The last response includes the exercise's `workouts` list; each workout
contains its `exercises` list, including association fields such as `reps` and
`sets`.

To test the `POST` endpoints, create an exercise and a workout:

```bash
curl -sS -X POST http://127.0.0.1:5555/exercises \
  -H "Content-Type: application/json" \
  -d '{"name":"Serialization Test","category":"Strength","equipment_needed":false}' \
  | python -m json.tool

curl -sS -X POST http://127.0.0.1:5555/workouts \
 -H "Content-Type: application/json" \
  -d '{"date":"2026-10-26","duration_minutes":30,"notes":"API test"}' \
  | python -m json.tool
```

Use the IDs returned by those commands to associate the exercise with the
workout. Replace `<workout_id>` and `<exercise_id>` with the actual numeric
IDs, without the angle brackets:

```bash
curl -sS -X POST \
  http://127.0.0.1:5555/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises \
  -H "Content-Type: application/json" \
  -d '{"reps":12,"sets":3}' \
  | python -m json.tool
```

### Example: create an exercise

```json
{
  "name": "Push-ups",
  "category": "Strength",
  "equipment_needed": false
}
```

### Example: create a workout

```json
{
  "date": "2026-10-22",
  "duration_minutes": 45,
  "notes": "Upper body"
}
```

### Example: add an exercise to a workout

```json
{
  "reps": 12,
  "sets": 3
}
```

## Dependencies

The project dependency manifest is [`Pipfile`](./Pipfile). Runtime packages:

- Flask `2.2.2`
- Flask-Migrate `3.1.0`
- Flask-SQLAlchemy `3.0.3`
- Werkzeug `2.2.2`
- importlib-metadata `6.0.0`
- importlib-resources `5.10.0`
- ipdb `0.13.9`
- Marshmallow `3.20.1`

Development test dependency:

- pytest

## Tests

Run the test suite from the repository root:

```bash
pipenv run pytest
```

API, model, and seed tests are in
[`server/test_workout_api.py`](./server/test_workout_api.py).
