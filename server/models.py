from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import validates

db = SQLAlchemy()

# Our entities are defined here. Each entity is a class that inherits from db.Model, which is the base class for all models in SQLAlchemy.
# Exercise,Workout,WorkoutExercises

class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category = db.Column(db.String, nullable=False)
    equipment_needed = db.Column(db.Boolean, default=False, nullable=False)

#Relationships
    workout_exercises = db.relationship('WorkoutExercises', back_populates='exercise', cascade='all, delete-orphan')
    workouts = db.relationship('Workout', secondary='workout_exercises', back_populates='exercises', viewonly=True)

    @validates('name')
    def validate_name(self, key, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Exercise name cannot be empty.")
        return name.strip()

    @validates('category')
    def validate_category(self, key, category):
        if not isinstance(category, str) or not category.strip():
            raise ValueError("Category cannot be empty.")

        normalized_category = category.strip().capitalize()
        allowed_categories = ['Strength', 'Cardio', 'Flexibility', 'Balance', 'Hiit']
        if normalized_category not in allowed_categories:
            raise ValueError(f"Category must be one of: {', '.join(allowed_categories)}")
        return normalized_category


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'equipment_needed': self.equipment_needed
        }

class Workout(db.Model):
    __tablename__ = 'workouts'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String, nullable=True)

    #Table Constraints (Requirement: > 1 working table constraint)
    __table_args__ = (
        CheckConstraint('duration_minutes > 0', name='check_duration_positive'),
        CheckConstraint("length(date) > 8", name='check_date_length')
    )


    # Relationships
    workout_exercises = db.relationship('WorkoutExercises', back_populates='workout', cascade='all, delete-orphan')
    exercises = db.relationship('Exercise', secondary='workout_exercises', back_populates='workouts', viewonly=True)

    @validates('date')
    def validate_date(self, key, value):
        if not isinstance(value, str):
            raise ValueError("Workout date must use YYYY-MM-DD format.")
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d")
        except ValueError as error:
            raise ValueError("Workout date must use YYYY-MM-DD format.") from error
        if parsed_date.strftime("%Y-%m-%d") != value:
            raise ValueError("Workout date must use YYYY-MM-DD format.")
        return value

    @validates('duration_minutes')
    def validate_duration(self, key, duration):
        if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
            raise ValueError("Workout duration must be a positive integer greater than 0.")
        return duration

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date,
            'duration_minutes': self.duration_minutes,
            'notes': self.notes,
            'exercises': [
                {
                    **workout_exercise.exercise.to_dict(),
                    'reps': workout_exercise.reps,
                    'sets': workout_exercise.sets,
                    'duration_seconds': workout_exercise.duration_seconds
                }
                for workout_exercise in self.workout_exercises
            ]
        }

class WorkoutExercises(db.Model):
    __tablename__ = 'workout_exercises'

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    reps = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)

    __table_args__ = (
        CheckConstraint('reps >= 0', name='check_reps_non_negative'),
        CheckConstraint('sets >= 0', name='check_sets_non_negative'),
        CheckConstraint(
            'duration_seconds >= 0',
            name='check_duration_seconds_non_negative'
        )
    )

    workout = db.relationship('Workout', back_populates='workout_exercises')
    exercise = db.relationship('Exercise', back_populates='workout_exercises')

    @validates('reps', 'sets', 'duration_seconds')
    def validate_non_negative_value(self, key, value):
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise ValueError(f"{key.replace('_', ' ').capitalize()} must be a non-negative integer.")
        return value

    def to_dict(self):
        return {
            "id": self.id,
            "workout_id": self.workout_id,
            "exercise_id": self.exercise_id,
            "reps": self.reps,
            "sets": self.sets,
            "duration_seconds": self.duration_seconds
        }