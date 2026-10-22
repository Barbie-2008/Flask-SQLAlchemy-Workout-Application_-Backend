from datetime import datetime

from marshmallow import Schema, ValidationError, fields, validates


class ExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    category = fields.Str(required=True)
    equipment_needed = fields.Bool(load_default=False)

    @validates("name")
    def validate_name(self, value):
        if not value.strip():
            raise ValidationError("Exercise name cannot be empty.")

    @validates("category")
    def validate_category(self, value):
        allowed = {"Strength", "Cardio", "Flexibility", "Balance", "Hiit"}
        if value.strip().capitalize() not in allowed:
            raise ValidationError(
                f"Category must be one of: {', '.join(sorted(allowed))}"
            )


class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Str(required=True)
    duration_minutes = fields.Int(required=True)
    notes = fields.Str(allow_none=True, load_default=None)

    @validates("date")
    def validate_date(self, value):
        try:
            parsed_date = datetime.strptime(value, "%Y-%m-%d")
        except ValueError as error:
            raise ValidationError("Date must use YYYY-MM-DD format.") from error
        if parsed_date.strftime("%Y-%m-%d") != value:
            raise ValidationError("Date must use YYYY-MM-DD format.")

    @validates("duration_minutes")
    def validate_duration(self, value):
        if value <= 0:
            raise ValidationError("Workout duration must be greater than 0 minutes.")


class WorkoutExercisesSchema(Schema):
    id = fields.Int(dump_only=True)
    workout_id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    reps = fields.Int(allow_none=True, load_default=None)
    sets = fields.Int(allow_none=True, load_default=None)
    duration_seconds = fields.Int(allow_none=True, load_default=None)

    @validates("reps")
    def validate_reps(self, value):
        self._validate_non_negative("Reps", value)

    @validates("sets")
    def validate_sets(self, value):
        self._validate_non_negative("Sets", value)

    @validates("duration_seconds")
    def validate_duration_seconds(self, value):
        self._validate_non_negative("Duration", value)

    @staticmethod
    def _validate_non_negative(label, value):
        if value is not None and value < 0:
            raise ValidationError(f"{label} cannot be negative.")


exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True)

workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True)

workout_exercises_schema = WorkoutExercisesSchema()
workout_exercises_list_schema = WorkoutExercisesSchema(many=True)
