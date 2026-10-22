import os

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from models import db, Exercise, Workout, WorkoutExercises
from schemas import exercise_schema, workout_exercises_schema, workout_schema

app = Flask(__name__)
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"sqlite:///{os.path.join(app.instance_path, 'app.db')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)
db.init_app(app)


def _load_json(schema, allow_empty=False):
    data = request.get_json(silent=True)
    if data is None and allow_empty and not request.data.strip():
        data = {}
    if not isinstance(data, dict):
        raise ValidationError({"_schema": ["Request body must be a JSON object."]})
    return schema.load(data)


def _validation_response(error):
    return jsonify({"errors": error.messages}), 400


@app.route('/')
def home():
    return jsonify({"message": "Welcome to the Workout Tracker API!"}), 200


@app.route('/workouts', methods=['GET'])
def get_workouts():
    return jsonify([workout.to_dict() for workout in Workout.query.all()]), 200


@app.route('/workouts/<int:workout_id>', methods=['GET'])
def get_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return jsonify({"error": "Workout not found"}), 404
    return jsonify(workout.to_dict()), 200


@app.route('/workouts', methods=['POST'])
def create_workout():
    try:
        data = _load_json(workout_schema)
    except ValidationError as error:
        return _validation_response(error)

    try:
        workout = Workout(**data)
        db.session.add(workout)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Workout violates a database constraint."}), 400
    return jsonify(workout.to_dict()), 201


@app.route('/workouts/<int:workout_id>', methods=['DELETE'])
def delete_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if workout is None:
        return jsonify({"error": "Workout not found"}), 404
    db.session.delete(workout)
    db.session.commit()
    return '', 204


@app.route('/exercises', methods=['GET'])
def get_exercises():
    return jsonify([exercise.to_dict() for exercise in Exercise.query.all()]), 200


@app.route('/exercises/<int:exercise_id>', methods=['GET'])
def get_exercise_by_id(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return jsonify({"error": "Exercise not found"}), 404

    exercise_data = exercise.to_dict()
    exercise_data["workouts"] = [
        workout.to_dict() for workout in exercise.workouts
    ]
    return jsonify(exercise_data), 200


@app.route('/exercises', methods=['POST'])
def create_exercise():
    try:
        data = _load_json(exercise_schema)
    except ValidationError as error:
        return _validation_response(error)

    try:
        exercise = Exercise(**data)
        db.session.add(exercise)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Exercise violates a database constraint."}), 400
    return jsonify(exercise.to_dict()), 201


@app.route('/exercises/<int:exercise_id>', methods=['DELETE'])
def delete_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if exercise is None:
        return jsonify({"error": "Exercise not found"}), 404
    db.session.delete(exercise)
    db.session.commit()
    return '', 204


@app.route(
    '/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises',
    methods=['POST']
)
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.session.get(Workout, workout_id)
    exercise = db.session.get(Exercise, exercise_id)
    if workout is None or exercise is None:
        return jsonify({"error": "Workout or Exercise not found"}), 404

    try:
        data = _load_json(workout_exercises_schema, allow_empty=True)
    except ValidationError as error:
        return _validation_response(error)

    workout_exercise = WorkoutExercises(
        workout_id=workout_id,
        exercise_id=exercise_id,
        **data
    )
    try:
        db.session.add(workout_exercise)
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Workout exercise violates a database constraint."}), 400
    return jsonify(workout_exercise.to_dict()), 201


if __name__ == '__main__':
    app.run(port=5555, debug=True)
