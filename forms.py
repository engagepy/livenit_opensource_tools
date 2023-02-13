from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Length


class first_user_form(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit !')


class gpt_form(FlaskForm):
    name = StringField(
        '',
        validators=[DataRequired(), Length(5,256)])
    submit = SubmitField('aiSearch')


class iss_form(FlaskForm):
    name = StringField("Name a Planet ? ", validators=[DataRequired()])
    submit = SubmitField('Fetch Space Data')


class weather_form(FlaskForm):
    city = StringField("Enter location, remember you can get specific.",
                       validators=[DataRequired()])

    submit = SubmitField('Get Weather')


class crypto_form(FlaskForm):
    symbol = StringField("Symbols Only (eg: btc, sol, eth )",
                         validators=[DataRequired(),
                                     Length(max=5)])
    submit = SubmitField('Crypto Update!')


class tax_form(FlaskForm):
    total = FloatField("Enter % Inclusive Amount: ",
                       validators=[DataRequired()])
    tax = FloatField("Enter %: ", validators=[DataRequired()])
    submit = SubmitField('Calculate!')


class flight_form(FlaskForm):
    departure = StringField("Enter Departure Airport Code: ",
                            validators=[DataRequired()])
    arrival = StringField("Enter Arrival Airport Code: ",
                          validators=[DataRequired()])
    submit = SubmitField('Rates and Dates!')


class airport_form(FlaskForm):
    airport = StringField("Enter Airport Code: ", validators=[DataRequired()])
    submit = SubmitField('Airport Data')


class superhero_form(FlaskForm):
    superhero = StringField("Enter Superhero Name / Real Name of Hero",
                            validators=[DataRequired()])
    submit = SubmitField('Super Fetch')


class prime_form(FlaskForm):
    name = StringField("Your Name To Activate ! ", validators=[DataRequired()])
    submit = SubmitField('Activate Prime Sequence')


class reverse_form(FlaskForm):
    name = StringField("Paste Text/Code Here ", validators=[DataRequired()])
    submit = SubmitField('Analyse')
