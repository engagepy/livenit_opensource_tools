import os
import iss
from flask import render_template, flash
import forms
from replit import db
from weathers import weather
from flight import flight_message
from crypto import coin
from primes import prime
from __main__ import app

@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/community', methods=['GET', 'POST'])
def user():
    name = None
    form = forms.first_user_form()
    user = []
    password = []
    email = []

    if form.validate_on_submit():
        name = form.name.data
        user.append(name)
        db["user"] += name
        form.name.data = ''
        email_id = form.email.data
        email.append(email_id)
        db["email"] += email
        form.email.data = ''
        passw = form.password.data
        password.append(passw)
        db['password'] += password
        form.password.data = ''
        flash("Cool, you're signed up ")
    return render_template('user.html', name=name, form=form)

@app.route('/iss', methods=['GET', 'POST'])
def iss_page():
    name = None
    form = forms.iss_form()
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
    form = forms.tax_form()

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

    form = forms.flight_form()

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
    form = forms.weather_form()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        x = weather(name)
        flash(x)


#os.system("python iss.py")
#iss.send_msg(number)
    return render_template('weather.html', name=name, form=form)

@app.route('/crypto', methods=['GET', 'POST'])
def btc():
    name = None
    form = forms.crypto_form()

    if form.validate_on_submit():
        name = "BTC"
        form.name.data = ''
        result = coin()
        flash(result[0])
        flash(result[1])
        flash(result[2])
        flash(result[3])
        flash(result[4])
        flash(result[5])
    return render_template('crypto.html', name=name, form=form)

@app.route('/prime', methods=['GET', 'POST'])
def prime_page():
    name = None
    form = forms.prime_form()

    if form.validate_on_submit():
        name = form.name.data
        form.name.data = " "
        result = prime()
        flash(result[1])
        flash("--------- ")
        flash(result[0])
    return render_template('prime.html', name=name, form=form)

@app.route('/nft', methods=['GET', 'POST'])
def nft():
    return render_template('nft.html')