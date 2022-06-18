from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, PasswordField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email


class first_user_form(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Submit !')


class iss_form(FlaskForm):
    name = StringField("Name a Planet ? ", validators=[DataRequired()])
    submit = SubmitField('Fetch Space Data')


class weather_form(FlaskForm):
    name = StringField("Enter Prominent City ", validators=[DataRequired()])
    submit = SubmitField('Get Weather')


class crypto_form(FlaskForm):
    name = StringField("Enter BitCoin Symbol (eg: 'btc' )",
                       validators=[DataRequired()])
    submit = SubmitField('BTC Update!')


class tax_form(FlaskForm):
    total = FloatField("Enter Tax Inclusive Amount: ",
                       validators=[DataRequired()])
    tax = FloatField("Enter Tax %: ", validators=[DataRequired()])
    submit = SubmitField('Calculate!')


class flight_form(FlaskForm):
    departure = StringField("Enter Departure Airport Code: ",
                            validators=[DataRequired()])
    arrival = StringField("Enter Arrival Airport Code: ",
                          validators=[DataRequired()])
    submit = SubmitField('Rates and Dates!')


class prime_form(FlaskForm):
    name = StringField("Your Name To Activate ! ", validators=[DataRequired()])
    submit = SubmitField('Activate Prime Sequence')