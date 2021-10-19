from flask import Flask, render_template, redirect, url_for, flash, abort, jsonify
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship
from forms import LoginForm, RegisterForm, NewProgramForm, NewWorkoutForm, AddExerciseForm, MakeProgramForm, ChangePasswordForm
from brain import Brain
from datetime import timedelta
from wtforms.fields import Label
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap(app)

# CONNECT TO DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///workout.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# CREATE BRAIN
brain = Brain()

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except ValueError:
        return None


# CONFIGURE TABLE

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(100))
    name = Column(String(100))
    program_templates = relationship("ProgramTemplate", back_populates="user")
    programs = relationship("Program", back_populates="user")


class ProgramTemplate(db.Model):
    __tablename__ = "programTemplates"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="program_templates")
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
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="programs")
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

# # CREATE TABLES THEN COMMENT OUT
# db.create_all()
#
# # POPULATE DAYS TABLE THEN COMMENT OUT
# days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
# for day in days:
#     new_day = Day(name=day)
#     db.session.add(new_day)
# db.session.commit()


# USER AUTHENTICATION


def protect_program_template(f):
    @wraps(f)
    def decorated_function(program_template_id, *args, **kwargs):
        requested_program_template = ProgramTemplate.query.get(program_template_id)
        if requested_program_template.user_id != current_user.id:
            return abort(403)
        return f(program_template_id, *args, **kwargs)
    return decorated_function


def protect_workout_template(f):
    @wraps(f)
    def decorated_function(workout_template_id, *args, **kwargs):
        requested_workout_template = WorkoutTemplate.query.get(workout_template_id)
        if requested_workout_template.parent_program_template.user_id != current_user.id:
            return abort(403)
        return f(workout_template_id, *args, **kwargs)
    return decorated_function


def protect_program(f):
    @wraps(f)
    def decorated_function(program_id, *args, **kwargs):
        requested_program = Program.query.get(program_id)
        if requested_program.user_id != current_user.id:
            return abort(403)
        return f(program_id, *args, **kwargs)
    return decorated_function


def protect_program_week(f):
    @wraps(f)
    def decorated_function(program_id, week, *args, **kwargs):
        requested_program = Program.query.get(program_id)
        if requested_program.user_id != current_user.id:
            return abort(403)
        return f(program_id, week, *args, **kwargs)
    return decorated_function


def protect_workout(f):
    @wraps(f)
    def decorated_function(workout_id, *args, **kwargs):
        requested_workout = Workout.query.get(workout_id)
        if requested_workout.parent_program.user_id != current_user.id:
            return abort(403)
        return f(workout_id, *args, **kwargs)
    return decorated_function


def protect_workout_week(f):
    @wraps(f)
    def decorated_function(workout_id, week, *args, **kwargs):
        requested_workout = Workout.query.get(workout_id)
        if requested_workout.parent_program.user_id != current_user.id:
            return abort(403)
        return f(workout_id, week, *args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET", "POST"])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()

        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('home', _anchor="login"))
        elif not check_password_hash(user.password, login_form.password.data):
            flash('Password incorrect, please try again.')
            return redirect(url_for('home', _anchor="login"))
        else:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template("index.html", form=login_form)

@app.route("/user", methods=["POST", "GET"])
def user():
    change_password_form = ChangePasswordForm()
    if change_password_form.validate_on_submit():
        if change_password_form.current_password.data != change_password_form.reenter.data:
            flash("Passwords do not match, re-enter your current password and try again.")
            return redirect(url_for('user'))
        elif not check_password_hash(current_user.password, change_password_form.current_password.data):
            flash('Wrong password.')
            return redirect(url_for('user'))
        else:
            hash_and_salted_password = generate_password_hash(
                change_password_form.new_password.data,
                method='pbkdf2:sha256',
                salt_length=8
            )
            setattr(current_user, 'password', hash_and_salted_password)
            db.session.commit()
            flash('Password successfully changed')
            return redirect(url_for('user'))
    return render_template("user.html", form=change_password_form)


# LOGIN/LOG OUT

@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        if User.query.filter_by(email=register_form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('home', _anchor="login"))

        hash_and_salted_password = generate_password_hash(
            register_form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            email=register_form.email.data,
            name=register_form.username.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("dashboard"))
    return render_template("register.html", form=register_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# SHOW


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    all_templates = ProgramTemplate.query.filter(ProgramTemplate.user_id == current_user.id).all()
    all_programs = Program.query.filter(Program.user_id == current_user.id).all()
    new_program_form = NewProgramForm()
    if new_program_form.validate_on_submit():
        new_program_template = ProgramTemplate(
            name=new_program_form.name.data,
            user=current_user
        )
        db.session.add(new_program_template)
        db.session.commit()
        return redirect(url_for("show_program_template", program_template_id=new_program_template.id))
    return render_template("dashboard.html", templates=all_templates, programs=all_programs, form=new_program_form)


@app.route("/program-templates/<int:program_template_id>", methods=["GET", "POST"])
@protect_program_template
def show_program_template(program_template_id):
    current_program_template = ProgramTemplate.query.get(program_template_id)

    # TABLE DATA

    daily_workouts = []
    most_workouts_in_one_day = 0
    for day_id in range(1, 8):
        day = Day.query.get(day_id)
        workouts = [workout_template for workout_template in current_program_template.workout_templates if day in workout_template.days]
        daily_workouts.append(workouts)
        if len(workouts) > most_workouts_in_one_day:
            most_workouts_in_one_day = len(workouts)

    workout_layers = []
    for num in range(most_workouts_in_one_day):
        workout_layer = []
        for workouts in daily_workouts:
            try:
                new_workout = workouts[num]
            except IndexError:
                workout_layer.append(0)
            else:
                workout_layer.append(new_workout)
        workout_layers.append(workout_layer)

    exercise_layers = []
    for workout_layer in workout_layers:
        most_exercises_in_layer = 0
        for element in workout_layer:
            if isinstance(element, WorkoutTemplate):
                if len(element.exercise_templates) > most_exercises_in_layer:
                    most_exercises_in_layer = len(element.exercise_templates)

        exercise_layer = []
        for row_number in range(most_exercises_in_layer):
            row = []
            for day_number in range(7):
                element = workout_layer[day_number]
                if isinstance(element, WorkoutTemplate):
                    try:
                        new_exercise = element.exercise_templates[row_number]
                    except IndexError:
                        row.append(0)
                    else:
                        row.append(f"{new_exercise.type} {len(new_exercise.set_templates)} x {new_exercise.set_templates[0].reps}")
                else:
                    row.append(0)
            exercise_layer.append(row)
        exercise_layers.append(exercise_layer)

    # FORM FUNCTIONALITY

    new_workout_form = NewWorkoutForm()
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
                           workout_layers=workout_layers,
                           exercise_layers=exercise_layers
                           )


@app.route("/workout-templates/<int:workout_template_id>", methods=["GET", "POST"])
@protect_workout_template
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

@app.route("/programs/<int:program_id>/week/<int:week>", methods=["GET", "POST"])
@protect_program_week
def show_program(program_id, week):
    current_program = Program.query.get(program_id)

    # CHECK IF CURRENT_WEEK HAS WORKOUTS
    earliest_workout_in_week = Workout.query.filter_by(parent_program=current_program, week=week).order_by(
        Workout.date).first()

    if not earliest_workout_in_week:
        earliest_workout_in_program = Workout.query.filter_by(parent_program=current_program).order_by(Workout.date).first()
        if not earliest_workout_in_program:
            return redirect(url_for('delete_program', program_id=current_program.id))
        last_workout_in_program = Workout.query.filter_by(parent_program=current_program).order_by(Workout.date.desc()).first()
        first_week = earliest_workout_in_program.week
        last_week = last_workout_in_program.week

        # UPDATE WEEKS AND REFRESH
        current_week = first_week
        week_update = 1
        while current_week <= last_week:
            workouts_in_week = Workout.query.filter_by(parent_program=current_program, week=current_week).all()
            if workouts_in_week:
                for workout in workouts_in_week:
                    setattr(workout, "week", week_update)
                week_update += 1
            current_week += 1
        setattr(current_program, "weeks", current_week - 1)
        db.session.commit()
        return redirect(url_for('show_program', program_id=program_id, week=last_week))

    # TABLE HEAD DATA

    first_day_of_week = earliest_workout_in_week.date
    while first_day_of_week.weekday() != 0:
        first_day_of_week -= timedelta(1)

    days_of_the_week = [(first_day_of_week + timedelta(num)).strftime("%a %m/%d/%y") for num in range(7)]

    # TABLE BODY DATA

    most_workouts_in_one_day = 0
    daily_workouts = []
    for day in range(7):
        workouts = [workout for workout in current_program.workouts if workout.week == week and workout.date.weekday() == day]
        if len(workouts) > most_workouts_in_one_day:
            most_workouts_in_one_day = len(workouts)
        daily_workouts.append(workouts)

    workout_layers = []
    for num in range(most_workouts_in_one_day):
        workout_layer = []
        for workouts in daily_workouts:
            try:
                new_workout = workouts[num]
            except IndexError:
                workout_layer.append(0)
            else:
                workout_layer.append(new_workout)
        workout_layers.append(workout_layer)

    exercise_layers = []
    for workout_layer in workout_layers:
        most_exercises_in_layer = 0
        for element in workout_layer:
            if isinstance(element, Workout):
                if len(element.exercises) > most_exercises_in_layer:
                    most_exercises_in_layer = len(element.exercises)

        exercise_layer = []
        for row_number in range(most_exercises_in_layer):
            row = []
            for day_number in range(7):
                element = workout_layer[day_number]
                if isinstance(element, Workout):
                    try:
                        new_exercise = element.exercises[row_number]
                    except IndexError:
                        row.append(0)
                    else:
                        exercise_weights = [set.weight for set in new_exercise.sets]
                        row.append(f"{new_exercise.type} {max(exercise_weights)} lbs. (max)")
                else:
                    row.append(0)
            exercise_layer.append(row)
        exercise_layers.append(exercise_layer)

    return render_template("show-program.html",
                           days_of_the_week=days_of_the_week,
                           program=current_program,
                           weeks=current_program.weeks,
                           current_week=week,
                           workout_layers=workout_layers,
                           exercise_layers=exercise_layers
                           )


@app.route("/workouts/<int:workout_id>", methods=["GET", "POST"])
@protect_workout
def show_workout(workout_id):
    requested_workout = Workout.query.get(workout_id)
    return render_template("show-workout.html", workout=requested_workout)


# DELETE


@app.route("/workout-templates/<int:workout_template_id>/delete")
@protect_workout_template
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
@protect_program_template
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
    return redirect(url_for('dashboard'))


@app.route("/week/<int:week>/workouts/<int:workout_id>/delete")
@protect_workout_week
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
@protect_program
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
    return redirect(url_for('dashboard'))


@app.route("/user/delete")
@login_required
def delete_user():
    for program_template in current_user.program_templates:
        for workout_template in program_template.workout_templates:
            for exercise_template in workout_template.exercise_templates:
                for set_template in exercise_template.set_templates:
                    db.session.delete(set_template)
                db.session.delete(exercise_template)
            db.session.delete(workout_template)
        db.session.delete(program_template)
    for program in current_user.programs:
        for workout in program.workouts:
            for exercise in workout.exercises:
                for set in exercise.sets:
                    db.session.delete(set)
                db.session.delete(exercise)
            db.session.delete(workout)
        db.session.delete(program)
    db.session.delete(current_user)
    db.session.commit()
    flash("Account deleted.")
    return redirect(url_for('home', _anchor="login"))


# MAKE PROGRAM


@app.route("/program-templates/<int:program_template_id>/make_program", methods=["GET", "POST"])
@protect_program_template
def make_program(program_template_id):
    requested_program_template = ProgramTemplate.query.get(program_template_id)

    exercises = []
    for workout_template in requested_program_template.workout_templates:
        for exercise_template in workout_template.exercise_templates:
            if exercise_template.type not in exercises:
                exercises.append(exercise_template.type)

    make_program_form = MakeProgramForm(
        name=requested_program_template.name,
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
            user=current_user,
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
    return render_template("make-program.html", form=make_program_form, template_id=program_template_id)


if __name__ == "__main__":
    app.run()
