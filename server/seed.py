from app import app
from models import db, Exercise, Workout, WorkoutExercises


def seed_data():
    with app.app_context():
        db.create_all()

        db.session.query(WorkoutExercises).delete()
        db.session.query(Workout).delete()
        db.session.query(Exercise).delete()

        exercises = [
            Exercise(name="Push-ups", category="Strength", equipment_needed=False),
            Exercise(name="Running", category="Cardio", equipment_needed=False),
            Exercise(name="Squats", category="Strength", equipment_needed=False)
        ]
        workouts = [
            Workout(
                date="2026-10-01",
                duration_minutes=45,
                notes="Morning upper body routine"
            ),
            Workout(
                date="2026-10-02",
                duration_minutes=30,
                notes="Cardio endurance session"
            )
        ]

        db.session.add_all(exercises + workouts)
        db.session.flush()
        db.session.add_all([
            WorkoutExercises(
                workout_id=workouts[0].id,
                exercise_id=exercises[0].id,
                reps=20,
                sets=3
            ),
            WorkoutExercises(
                workout_id=workouts[0].id,
                exercise_id=exercises[2].id,
                reps=15,
                sets=4
            ),
            WorkoutExercises(
                workout_id=workouts[1].id,
                exercise_id=exercises[1].id,
                duration_seconds=1800
            )
        ])
        db.session.commit()
        print("Seeding complete successfully!")


if __name__ == "__main__":
    seed_data()
