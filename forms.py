from flask_wtf import FlaskForm, Form
from wtforms import StringField, SubmitField, PasswordField, IntegerField, SelectField, SelectMultipleField, DateField, FieldList, FormField
from wtforms.validators import DataRequired, Optional

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Log in")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    register = SubmitField("Register")

class NewProgramForm(FlaskForm):
    name = StringField("Template's name", validators=[DataRequired()])
    create = SubmitField("Create template")

class NewWorkoutForm(FlaskForm):
    name = StringField("Workout's name", validators=[DataRequired()])
    days = SelectMultipleField(
        "Days of the week",
        choices=[
                ('1', 'Monday'),
                ('2', 'Tuesday'),
                ('3', 'Wednesday'),
                ('4', 'Thursday'),
                ('5', 'Friday'),
                ('6', 'Saturday'),
                ('7', 'Sunday'),
            ],
        validators=[DataRequired()])
    add = SubmitField("Add")

class AddExerciseForm(FlaskForm):
    type = SelectField("Exercise type", choices=["Deadlift", "Bench press", "Overhead press"])
    sets = IntegerField("Sets", validators=[DataRequired()])
    reps_per_set = IntegerField("Reps per set", validators=[DataRequired()])
    add = SubmitField("Add exercise")

class SetWeightsForm(Form):
    starting_weight = IntegerField("Starting weight", validators=[DataRequired()])
    increment = IntegerField("Weight increment (per session)", validators=[DataRequired()])

class MakeProgramForm(FlaskForm):
    name = StringField("Program's name", validators=[DataRequired()])
    weeks = IntegerField("Duration (in weeks)", validators=[DataRequired()])
    starting_date = DateField("Starting date", format='%d/%m/%Y', validators=[DataRequired()])
    exercises = FieldList(FormField(SetWeightsForm))
    make = SubmitField("Make program")

