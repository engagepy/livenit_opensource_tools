from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, PasswordField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email, Length


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
    city = StringField("Enter location, remember you can get specific.", validators=[DataRequired()])

    
    submit = SubmitField('Get Weather')


class crypto_form(FlaskForm):
    symbol = StringField("Symbols Only (eg: btc, sol, eth )",
                       validators=[DataRequired(), Length(max=5)])
    submit = SubmitField('Crypto Update!')


class tax_form(FlaskForm):
    total = FloatField("Enter % Inclusive Amount: ",
                       validators=[DataRequired()])
    tax = FloatField("Enter %: ", validators=[DataRequired()])
    submit = SubmitField('Calculate!')


class iti_form(FlaskForm):
    room = FloatField("Rooms Cost Avg ",
                       validators=[DataRequired()])
    nights = FloatField("Stay Nights Exact ", validators=[DataRequired()])
    pax = FloatField("Total Pax Count", validators=[DataRequired()])
    scuba_boat = FloatField("Scuba Boat Cost")
    scuba_shore = FloatField("Scuba Shore Cost")
    kayak = FloatField('Kayaking Cost')
    transfer_hv_pb = FloatField('Transfer Cost')
    submit = SubmitField('Calculate!')
    

class flight_form(FlaskForm):
    departure = StringField("Enter Departure Airport Code: ",
                            validators=[DataRequired()])
    arrival = StringField("Enter Arrival Airport Code: ",
                          validators=[DataRequired()])
    submit = SubmitField('Rates and Dates!')

class airport_form(FlaskForm):
    airport = StringField("Enter Airport Code: ",
                            validators=[DataRequired()])
    submit = SubmitField('Airport Data')


class prime_form(FlaskForm):
    name = StringField("Your Name To Activate ! ", validators=[DataRequired()])
    submit = SubmitField('Activate Prime Sequence')

class reverse_form(FlaskForm):
    name = StringField("Paste Text Here ", validators=[DataRequired()])
    submit = SubmitField('Analyse Text')