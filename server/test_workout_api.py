import pytest
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError

from app import app
from models import db, Exercise, Workout, WorkoutExercises
from seed import seed_data

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_model_validations(client):
    with app.app_context():
        # Test Exercise name validation
        with pytest.raises(ValueError, match="Exercise name cannot be empty"):
            ex = Exercise(name="", category="Strength")
            db.session.add(ex)
            db.session.commit()
        db.session.rollback()

        # Test Exercise category validation
        with pytest.raises(ValueError, match="Category must be one of"):
            ex = Exercise(name="Plank", category="InvalidCategory")
            db.session.add(ex)
            db.session.commit()
        db.session.rollback()

        # Test Workout duration validation
        with pytest.raises(ValueError, match="Workout duration must be a positive integer"):
            workout = Workout(date="2026-10-22", duration_minutes=0)
            db.session.add(workout)
            db.session.commit()
        db.session.rollback()

        with pytest.raises(ValueError, match="Workout date must use YYYY-MM-DD format"):
            Workout(date="not-a-date", duration_minutes=30)

        with pytest.raises(ValueError, match="non-negative integer"):
            WorkoutExercises(reps=-1)

def test_relationships(client):
    with app.app_context():
        ex = Exercise(name="Bench Press", category="Strength")
        workout = Workout(date="2026-10-22", duration_minutes=45, notes="Chest day")
        db.session.add_all([ex, workout])
        db.session.commit()

        we = WorkoutExercises(workout_id=workout.id, exercise_id=ex.id, reps=10, sets=3)
        db.session.add(we)
        db.session.commit()

        assert len(workout.workout_exercises) == 1
        assert workout.workout_exercises[0].exercise.name == "Bench Press"
        assert len(ex.workout_exercises) == 1
        assert ex.workout_exercises[0].workout.duration_minutes == 45

def test_api_endpoints_workflow(client):
    # Test GET /exercises empty
    res = client.get('/exercises')
    assert res.status_code == 200
    assert res.get_json() == []

    # Test POST /exercises
    res = client.post('/exercises', json={
        "name": "Deadlift",
        "category": "Strength",
        "equipment_needed": True
    })
    assert res.status_code == 201
    ex_data = res.get_json()
    ex_id = ex_data["id"]
    assert ex_data["name"] == "Deadlift"
    res = client.get('/exercises')
    assert res.status_code == 200
    assert res.get_json()[0]["id"] == ex_id

    # Test POST /workouts
    res = client.post('/workouts', json={
        "date": "2026-10-22",
        "duration_minutes": 50,
        "notes": "Leg day"
    })
    assert res.status_code == 201
    workout_data = res.get_json()
    workout_id = workout_data["id"]
    assert workout_data["duration_minutes"] == 50
    res = client.get('/workouts')
    assert res.status_code == 200
    assert res.get_json()[0]["id"] == workout_id

    # Test POST join table endpoint
    res = client.post(f'/workouts/{workout_id}/exercises/{ex_id}/workout_exercises', json={
        "reps": 5,
        "sets": 5
    })
    assert res.status_code == 201

    # Test GET /workouts/<id> with nested exercises inclusion
    res = client.get(f'/workouts/{workout_id}')
    assert res.status_code == 200
    full_workout = res.get_json()
    assert len(full_workout["exercises"]) == 1
    assert full_workout["exercises"][0]["name"] == "Deadlift"
    assert full_workout["exercises"][0]["reps"] == 5
    assert full_workout["exercises"][0]["sets"] == 5

    res = client.get(f'/exercises/{ex_id}')
    assert res.status_code == 200
    assert res.get_json()["workouts"][0]["id"] == workout_id

    # Test DELETE /workouts/<id>
    res = client.delete(f'/workouts/{workout_id}')
    assert res.status_code == 204
    assert client.get(f'/workouts/{workout_id}').status_code == 404
    assert client.delete(f'/exercises/{ex_id}').status_code == 204


def test_missing_resources_return_404(client):
    assert client.get('/workouts/999').status_code == 404
    assert client.delete('/workouts/999').status_code == 404
    assert client.get('/exercises/999').status_code == 404
    assert client.delete('/exercises/999').status_code == 404
    assert client.post(
        '/workouts/999/exercises/999/workout_exercises',
        json={"reps": 1}
    ).status_code == 404


def test_api_schemas_reject_invalid_input(client):
    invalid_exercise = client.post('/exercises', json={
        "name": " ",
        "category": "Invalid"
    })
    assert invalid_exercise.status_code == 400
    assert "errors" in invalid_exercise.get_json()

    invalid_workout = client.post('/workouts', json={
        "date": "not-a-date",
        "duration_minutes": 0
    })
    assert invalid_workout.status_code == 400
    assert "errors" in invalid_workout.get_json()

    exercise = client.post('/exercises', json={
        "name": "Plank",
        "category": "Strength"
    }).get_json()
    workout = client.post('/workouts', json={
        "date": "2026-10-22",
        "duration_minutes": 30
    }).get_json()

    invalid_association = client.post(
        f'/workouts/{workout["id"]}/exercises/{exercise["id"]}/workout_exercises',
        json={"reps": -1}
    )
    assert invalid_association.status_code == 400
    assert "errors" in invalid_association.get_json()


def test_database_constraints_reject_invalid_values(client):
    with app.app_context():
        with pytest.raises(IntegrityError):
            db.session.execute(insert(Workout).values(
                date="2026-10-22",
                duration_minutes=0
            ))
        db.session.rollback()

        with pytest.raises(IntegrityError):
            db.session.execute(insert(Workout).values(
                date="x",
                duration_minutes=30
            ))
        db.session.rollback()

        workout = Workout(date="2026-10-22", duration_minutes=30)
        exercise = Exercise(name="Plank", category="Strength")
        db.session.add_all([workout, exercise])
        db.session.commit()

        for invalid_values in (
            {"reps": -1},
            {"sets": -1},
            {"duration_seconds": -1}
        ):
            with pytest.raises(IntegrityError):
                db.session.execute(insert(WorkoutExercises).values(
                    workout_id=workout.id,
                    exercise_id=exercise.id,
                    **invalid_values
                ))
            db.session.rollback()


def test_seed_creates_all_model_types(client):
    seed_data()
    with app.app_context():
        assert Exercise.query.count() == 3
        assert Workout.query.count() == 2
        assert WorkoutExercises.query.count() == 3
