import os 
import iss
from flask import Flask, render_template, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, PasswordField, BooleanField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email
from replit import db
from weathers import weather
from flight import flight_message

my_secret = os.environ['SECRET_KEY']
id_key = 0

app = Flask(__name__)
app.config['SECRET_KEY'] = my_secret

Bootstrap(app)

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

@app.route('/')
def index():
	return render_template('landing.html')

@app.route('/user', methods=['GET', 'POST'])
def user():
	name = None
	form = first_user_form()
	user = []
	user.append(db["user"])

	email = []
	email.append(db["email"])

	if form.validate_on_submit():

		name = form.name.data
		user.append(name)
		db["user"] = user
		form.name.data = ''

		email_id = form.email.data
		email.append(email_id)
		db["email"] = email
		form.email.data = ''
		flash("Cool, you're signed up ")
	return render_template('user.html', name=name, form=form)

@app.route('/iss', methods=['GET', 'POST'])
def iss_page():
  name = None
  form = iss_form()
  if form.validate_on_submit():
    os.system('python iss.py')
    name = form.name.data
    form.name.data = ''
    flash(iss.message())
  return render_template('iss.html', name=name, form=form)

@app.route('/tax', methods=['GET', 'POST'])
def tax_page():
	total = 0
	tax = 0
	pre_tax = 0
	tax_amount = 0
	form = tax_form()

	if form.validate_on_submit():
		total = form.total.data
		form.total.data = ''
		tax = form.tax.data
		tax_1 = (tax + 100) / 100
		form.tax.data = ''

		pre_tax = total / tax_1
		tax_amount = total - pre_tax

		flash('Total, Tax, Pre-Tax Total & Tax Amount - That Easy! Refer Us. ')

	return render_template('tax.html',
	                       total=total,
	                       tax=tax,
	                       pre_tax=round(pre_tax, 2),
	                       tax_amount=round(tax_amount, 2),
	                       form=form)

@app.route('/flight', methods=['GET', 'POST'])
def flight_page():
	arrival = None
	departure = None

	form = flight_form()

	if form.validate_on_submit():
		departure = form.departure.data
		form.departure.data = ''
		arrival = form.arrival.data
		form.arrival.data = ''
		x = flight_message(arrival, departure)
		flash(x[0])
		flash(x[1])
		#os.system("python iss.py")
		#iss.send_msg(number)
	return render_template('flights.html',
	                       arrival=arrival,
	                       departure=departure,
	                       form=form)

@app.route('/weathers', methods=['GET', 'POST'])
def weathery():

  name = None
  form = weather_form()
  if form.validate_on_submit():
    name = form.name.data
    form.name.data = ''
    x = weather(name)
    flash(x)
		#os.system("python iss.py")
		#iss.send_msg(number)
  return render_template('weather.html',name=name,
	                       form=form)

if __name__ == '__main__':
	app.run(debug=False, host='0.0.0.0', port=8080)
