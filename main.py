from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from forms import LoginForm, RegisterForm, NewProgramForm, NewWorkoutForm, AddExerciseForm, MakeProgramForm
from brain import Brain
from datetime import timedelta
from wtforms.fields import Label

app = Flask(__name__)
app.config['SECRET_KEY'] = "hola"
Bootstrap(app)

# CONNECT TO DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///workout.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# CREATE BRAIN
brain = Brain()

# TODO create/configure User, Program, Workout and Set tables
# DONE 1 Create Program-Workout relationship
# DONE 2 Make child Set class
# DONE 3 Create Workout-Set relationship
# TODO 4 make User class
# TODO 5 create User-Prorgram relationship


class ProgramTemplate(db.Model):
    __tablename__ = "programTemplates"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    workout_templates = relationship("WorkoutTemplate", back_populates="parent_program_template")


class WorkoutTemplate(db.Model):
    __tablename__ = "workoutTemplates"
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    program_template_id = Column(Integer, ForeignKey("programTemplates.id"))
    parent_program_template = relationship("ProgramTemplate", back_populates="workout_templates")
    exercise_templates = relationship("ExerciseTemplate", back_populates="parent_workout_template")
    days = relationship('Day',
                        secondary="workoutdays",
                        back_populates="workout_templates")


class Day(db.Model):
    __tablename__ = "days"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    workout_templates = relationship('WorkoutTemplate',
                                     secondary="workoutdays",
                                     back_populates="days")


class WorkoutDay(db.Model):
    __tablename__ = 'workoutdays'
    workout_id = Column(
        Integer,
        ForeignKey('workoutTemplates.id'),
        primary_key=True)
    day_id = Column(
        Integer,
        ForeignKey('days.id'),
        primary_key=True)


class ExerciseTemplate(db.Model):
    __tablename__ = "exerciseTemplates"
    id = Column(Integer, primary_key=True)
    type = Column(String(200), nullable=False)
    workout_template_id = Column(Integer, ForeignKey("workoutTemplates.id"))
    parent_workout_template = relationship("WorkoutTemplate", back_populates="exercise_templates")
    set_templates = relationship("SetTemplate", back_populates="parent_exercise_template")


class SetTemplate(db.Model):
    __tablename__ = "setTemplates"
    id = Column(Integer, primary_key=True)
    reps = Column(Integer, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exerciseTemplates.id"))
    parent_exercise_template = relationship("ExerciseTemplate", back_populates="set_templates")


class Program(db.Model):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    weeks = Column(Integer, nullable=False)
    workouts = relationship("Workout", back_populates="parent_program")


class Workout(db.Model):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    week = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"))
    parent_program = relationship("Program", back_populates="workouts")
    exercises = relationship("Exercise", back_populates="parent_workout")


class Exercise(db.Model):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True)
    type = Column(String(200), nullable=False)
    workout_id = Column(Integer, ForeignKey("workouts.id"))
    parent_workout = relationship("Workout", back_populates="exercises")
    sets = relationship("Set", back_populates="parent_exercise")


class Set(db.Model):
    __tablename__ = "sets"
    id = Column(Integer, primary_key=True)
    weight = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    order = Column(Integer, nullable=False)
    completed = Column(Boolean, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    parent_exercise = relationship("Exercise", back_populates="sets")

# # CREATE DB THEN COMMENT OUT
# db.create_all()
#
# # POPULATE DAYS TABLE THEN COMMENT OUT
# monday = Day(name="Monday")
# tuesday = Day(name="Tuesday")
# wednesday = Day(name="Wednesday")
# thursday = Day(name="Thursday")
# friday = Day(name="Friday")
# saturday = Day(name="Saturday")
# sunday = Day(name="Sunday")
# db.session.add(monday)
# db.session.add(tuesday)
# db.session.add(wednesday)
# db.session.add(thursday)
# db.session.add(friday)
# db.session.add(saturday)
# db.session.add(sunday)
# db.session.commit()
# TODO implement login manager


@app.route("/", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        # TODO check that email exists and password matches
        # TODO login user
        return redirect(url_for('all'))
    return render_template("login.html", form=login_form)


@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        # TODO create user and add it to the database
        # TODO login user
        return redirect(url_for('all'))
    return render_template("register.html", form=register_form)


@app.route("/all", methods=["GET", "POST"])
def all():
    all_templates = ProgramTemplate.query.all()
    all_programs = Program.query.all()
    new_program_form = NewProgramForm(name="My template")
    if new_program_form.validate_on_submit():
        new_program_template = ProgramTemplate(name=new_program_form.name.data)
        db.session.add(new_program_template)
        db.session.commit()
        return redirect(url_for("show_program_template", program_template_id=new_program_template.id))
    return render_template("all.html", templates=all_templates, programs=all_programs, form=new_program_form)


# SHOW


@app.route("/program-templates/<int:program_template_id>", methods=["GET", "POST"])
def show_program_template(program_template_id):
    current_program_template = ProgramTemplate.query.get(program_template_id)

    weekly_workouts = []
    most_workouts_in_one_day = 0
    for day_id in range(1, 8):
        day = Day.query.get(day_id)
        daily_workouts = [workout_template for workout_template in current_program_template.workout_templates if day in workout_template.days]
        weekly_workouts.append(daily_workouts)
        if len(daily_workouts) > most_workouts_in_one_day:
            most_workouts_in_one_day = len(daily_workouts)

    new_workout_form = NewWorkoutForm(
        name="My workout"
    )
    if new_workout_form.validate_on_submit():
        day_ids = new_workout_form.days.data
        selected_days = [Day.query.get(day_id) for day_id in day_ids]
        new_workout_template = WorkoutTemplate(
            name=new_workout_form.name.data,
            parent_program_template=current_program_template,
            days=selected_days
        )
        db.session.add(new_workout_template)
        db.session.commit()
        return redirect(url_for('show_workout_template', workout_template_id=new_workout_template.id))
    return render_template("show-program-template.html",
                           form=new_workout_form,
                           template=current_program_template,
                           rows=most_workouts_in_one_day,
                           monday_workouts=weekly_workouts[0],
                           tuesday_workouts=weekly_workouts[1],
                           wednesday_workouts=weekly_workouts[2],
                           thursday_workouts=weekly_workouts[3],
                           friday_workouts=weekly_workouts[4],
                           saturday_workouts=weekly_workouts[5],
                           sunday_workouts=weekly_workouts[6]
                           )


@app.route("/workout-templates/<int:workout_template_id>", methods=["GET", "POST"])
def show_workout_template(workout_template_id):
    current_workout_template = WorkoutTemplate.query.get(workout_template_id)
    add_exercise_form = AddExerciseForm()
    if add_exercise_form.validate_on_submit():
        new_exercise_template = ExerciseTemplate(
            type=add_exercise_form.type.data,
            parent_workout_template=current_workout_template)
        db.session.add(new_exercise_template)
        db.session.commit()

        number_of_sets = add_exercise_form.sets.data
        reps_per_set = add_exercise_form.reps_per_set.data
        for num in range(number_of_sets):
            new_set_template = SetTemplate(
                reps=reps_per_set,
                parent_exercise_template=new_exercise_template
            )
            db.session.add(new_set_template)
            db.session.commit()

        return redirect(url_for("show_workout_template", workout_template_id=current_workout_template.id))
    return render_template("show-workout-template.html", workout=current_workout_template, form=add_exercise_form)


@app.route("/programs/<int:program_id>/week/<int:week>")
def show_program(program_id, week):
    current_program = Program.query.get(program_id)

    most_workouts_in_one_day = 0
    weekly_workouts = []
    for day in range(7):
        daily_workouts = [workout for workout in current_program.workouts if workout.week == week and workout.date.weekday() == day]
        if len(daily_workouts) > most_workouts_in_one_day:
            most_workouts_in_one_day = len(daily_workouts)
        weekly_workouts.append(daily_workouts)

    earliest_workout = Workout.query.filter(Workout.week==week).group_by(Workout.date).first()

    first_day_of_week = earliest_workout.date
    while first_day_of_week.weekday() != 0:
        first_day_of_week -= timedelta(1)

    days_of_the_week = [(first_day_of_week + timedelta(num)).strftime("%a %m/%d/%y") for num in range(7)]

    return render_template("show-program.html",
                           days_of_the_week=days_of_the_week,
                           program=current_program,
                           number_of_rows=most_workouts_in_one_day,
                           monday_workouts=weekly_workouts[0],
                           tuesday_workouts=weekly_workouts[1],
                           wednesday_workouts=weekly_workouts[2],
                           thursday_workouts=weekly_workouts[3],
                           friday_workouts=weekly_workouts[4],
                           saturday_workouts=weekly_workouts[5],
                           sunday_workouts=weekly_workouts[6],
                           current_week=week,
                           weeks=current_program.weeks
                           )


@app.route("/workouts/<int:workout_id>", methods=["GET", "POST"])
def show_workout(workout_id):
    requested_workout = Workout.query.get(workout_id)
    return render_template("show-workout.html", workout=requested_workout)


# DELETE


@app.route("/workout-templates/<int:workout_template_id>/delete")
def delete_workout_template(workout_template_id):
    requested_workout_template = WorkoutTemplate.query.get(workout_template_id)
    parent_program_template_id = requested_workout_template.program_template_id
    for exercise_template in requested_workout_template.exercise_templates:
        for set_template in exercise_template.set_templates:
            db.session.delete(set_template)
        db.session.delete(exercise_template)
    db.session.delete(requested_workout_template)
    db.session.commit()
    return redirect(url_for('show_program_template', program_template_id=parent_program_template_id))


@app.route("/program-templates/<int:program_template_id>/delete")
def delete_program_template(program_template_id):
    requested_program_template = ProgramTemplate.query.get(program_template_id)
    for workout_template in requested_program_template.workout_templates:
        for exercise_template in workout_template.exercise_templates:
            for set_template in exercise_template.set_templates:
                db.session.delete(set_template)
            db.session.delete(exercise_template)
        db.session.delete(workout_template)
    db.session.delete(requested_program_template)
    db.session.commit()
    return redirect(url_for('all'))


@app.route("/week/<int:week>/workouts/<int:workout_id>/delete")
def delete_workout(workout_id, week):
    requested_workout = Workout.query.get(workout_id)
    parent_program_id = requested_workout.program_id
    for exercise in requested_workout.exercises:
        for set in exercise.sets:
            db.session.delete(set)
        db.session.delete(exercise)
    db.session.delete(requested_workout)
    db.session.commit()
    return redirect(url_for('show_program', program_id=parent_program_id, week=week))


@app.route("/programs/<int:program_id>/delete")
def delete_program(program_id):
    requested_program = Program.query.get(program_id)
    for workout in requested_program.workouts:
        for exercise in workout.exercises:
            for set in exercise.sets:
                db.session.delete(set)
            db.session.delete(exercise)
        db.session.delete(workout)
    db.session.delete(requested_program)
    db.session.commit()
    return redirect(url_for('all'))


# MAKE PROGRAM


@app.route("/program-templates/<int:program_template_id>/make_program", methods=["GET", "POST"])
def make_program(program_template_id):
    requested_program_template = ProgramTemplate.query.get(program_template_id)

    exercises = []
    for workout_template in requested_program_template.workout_templates:
        for exercise_template in workout_template.exercise_templates:
            if exercise_template.type not in exercises:
                exercises.append(exercise_template.type)

    make_program_form = MakeProgramForm(
        exercises=exercises
    )

    for count, value in enumerate(make_program_form.exercises):
        value.label = Label(field_id=value.id, text=exercises[count])
        value.name = exercises[count]

    if make_program_form.validate_on_submit():

        starting_weights = {entry.name: entry.starting_weight.data for entry in make_program_form.exercises}
        increments = {entry.name: entry.increment.data for entry in make_program_form.exercises}
        dummy_program = brain.make_dummy_program(
            program_template=requested_program_template,
            starting_date=make_program_form.starting_date.data,
            weeks=make_program_form.weeks.data,
            starting_weights=starting_weights,
            increments=increments
            )
        new_program = Program(
            name=make_program_form.name.data,
            weeks=dummy_program.weeks
        )
        db.session.add(new_program)
        for dummy_workout in dummy_program.workouts:
            new_workout = Workout(
                name=dummy_workout.name[0],
                week=dummy_workout.week[0],
                date=dummy_workout.date[0],
                parent_program=new_program
            )
            db.session.add(new_workout)
            for dummy_exercise in dummy_workout.exercises:
                new_exercise = Exercise(
                    type=dummy_exercise.type[0],
                    parent_workout=new_workout
                )
                db.session.add(new_exercise)
                for dummy_set in dummy_exercise.sets:
                    new_set = Set(
                        weight=dummy_set.weight[0],
                        reps=dummy_set.reps[0],
                        order=dummy_set.order[0],
                        completed=False,
                        parent_exercise=new_exercise
                    )
                    db.session.add(new_set)
        db.session.commit()
        return redirect(url_for('show_program', program_id=new_program.id, week=1))
    return render_template("make-program.html", form=make_program_form)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
