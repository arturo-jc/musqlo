from datetime import timedelta


class DummyProgram:
    def __init__(self, starting_date, weeks, starting_weights, increments):
        self.starting_date = starting_date
        self.weeks = weeks
        self.starting_weights = starting_weights
        self.increments = increments
        self.increment_frequency = 0
        self.smallest_weight_plate = 0
        self.workouts = []


class DummyWorkout:
    def __init__(self, name, week, date, parent_program):
        self.name = name,
        self.week = week,
        self.date = date,
        self.parent_program = parent_program,
        self.exercises = []


class DummyExercise:
    def __init__(self, exercise_type):
        self.type = exercise_type,
        self.sets = []


class DummySet:
    def __init__(self, weight, reps, order):
        self.weight = weight,
        self.reps = reps,
        self.order = order,


class Brain:
    def make_dummy_program(self, program_template, starting_date, weeks, starting_weights, increments):
        new_program = DummyProgram(
            starting_date=starting_date,
            weeks=weeks,
            starting_weights=starting_weights,
            increments=increments
        )

        week = 1
        first_pass = True
        while week <= new_program.weeks:
            while week == 1:
                if first_pass:
                    # Find first and last days of current week
                    first_day_of_the_week = new_program.starting_date
                    last_day_of_the_week = first_day_of_the_week
                    while last_day_of_the_week.weekday() != 6:
                        last_day_of_the_week += timedelta(1)

                for workout_template in program_template.workout_templates:
                    for day in workout_template.days:
                        workout_date = first_day_of_the_week
                        while workout_date != last_day_of_the_week:
                            if day.id - 1 == workout_date.weekday():
                                new_workout = self.make_dummy_workout(
                                    workout_template=workout_template,
                                    program=new_program,
                                    week=week,
                                    date=workout_date
                                )
                                self.update_weights(new_workout)
                                break
                            workout_date += timedelta(1)

                # Check if any dummy workouts were created
                if new_program.workouts:
                    week += 1
                else:
                    first_day_of_the_week = last_day_of_the_week + timedelta(1)
                    last_day_of_the_week = first_day_of_the_week + timedelta(6)
                    first_pass = False

            first_day_of_the_week = last_day_of_the_week + timedelta(1)
            last_day_of_the_week = first_day_of_the_week + timedelta(6)

            for workout_template in program_template.workout_templates:
                for day in workout_template.days:
                    workout_date = first_day_of_the_week
                    while workout_date != last_day_of_the_week:
                        if day.id - 1 == workout_date.weekday():
                            new_workout = self.make_dummy_workout(
                                workout_template=workout_template,
                                program=new_program,
                                week=week,
                                date=workout_date
                            )
                            self.update_weights(new_workout)
                            break
                        workout_date += timedelta(1)
            week += 1
        return new_program

    def make_dummy_workout(self, workout_template, program, week, date):
        new_workout = DummyWorkout(
            name=workout_template.name,
            week=week,
            date=date,
            parent_program=program
        )
        program.workouts.append(new_workout)
        for exercise_template in workout_template.exercise_templates:
            new_exercise = DummyExercise(
                exercise_type=exercise_template.type,
            )
            new_workout.exercises.append(new_exercise)
            set_order = 1
            for set_template in exercise_template.set_templates:
                weight = program.starting_weights[new_exercise.type[0]]
                new_set = DummySet(
                    weight=weight,  # TODO Finesse
                    reps=set_template.reps,
                    order=set_order
                )
                set_order += 1
                new_exercise.sets.append(new_set)
        return new_workout

    def update_weights(self, workout):
        for exercise in workout.exercises:
            workout.parent_program[0].starting_weights[exercise.type[0]] += workout.parent_program[0].increments[exercise.type[0]]