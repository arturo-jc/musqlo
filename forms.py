from flask_wtf import FlaskForm, Form
from wtforms import StringField, SubmitField, PasswordField, IntegerField, SelectField, SelectMultipleField, FieldList, FormField
from wtforms.widgets import ListWidget, CheckboxInput
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()], render_kw={'autofocus': True})
    password = PasswordField("Password", validators=[DataRequired()])
    login = SubmitField("Log in")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()], render_kw={'autofocus': True})
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    register = SubmitField("Register")


class NewProgramForm(FlaskForm):
    name = StringField("Template's name", validators=[DataRequired()])
    create = SubmitField("Create template")


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class NewWorkoutForm(FlaskForm):
    name = StringField("Workout's name", validators=[DataRequired()])
    days = MultiCheckboxField(
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
    starting_weight = IntegerField("Starting weight", validators=[DataRequired()], render_kw={"class": "form-control"})
    increment = IntegerField("Weight increment (per session)", validators=[DataRequired()], render_kw={"class": "form-control"})


class MakeProgramForm(FlaskForm):
    name = StringField("Program's name", validators=[DataRequired()])
    weeks = IntegerField("Duration (in weeks)", validators=[DataRequired()])
    starting_date = DateField("Starting date", format='%Y-%m-%d', validators=[DataRequired()])
    exercises = FieldList(FormField(SetWeightsForm))
    make = SubmitField("Make program")

class TestForm(FlaskForm):
    test = SubmitField("Test")
