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
        name = form.name.data.strip()
        user.append(name)
        db["user"] += name
        form.name.data = ''
        email_id = form.email.data.strip()
        email.append(email_id)
        db["email"] += email
        form.email.data = ''
        passw = form.password.data.strip()
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
        name = form.name.data.strip()
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
        departure = form.departure.data.strip()
        form.departure.data = ''
        arrival = form.arrival.data.strip()
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

    city = None
    form = forms.weather_form()
    if form.validate_on_submit():
        city = form.city.data.strip()
        form.city.data = None
        x = weather(city)
        print(x)
        for i in x[0:]:
          flash(i)
        #flash(x)[0]
        #flash(x)[1]
        


#os.system("python iss.py")
#iss.send_msg(number)
    return render_template('weather.html', city=city, form=form)

@app.route('/crypto', methods=['GET', 'POST'])
def btc():
    symbol = None
    form = forms.crypto_form()
    if form.validate_on_submit():
        symbol = form.symbol.data.strip()
        form.symbol.data = ''
        result = coin(symbol)
        flash(result[0])
        flash(result[1])
        flash(result[2])
        flash(result[3])
        flash(result[4])
        flash(result[5])
        print("btc_run")
    return render_template('crypto.html', symbol=symbol, form=form)

@app.route('/prime', methods=['GET', 'POST'])
def prime_page():
    name = None
    form = forms.prime_form()
    count = None
    mathops = None

    if form.validate_on_submit():
        name = form.name.data
        form.name.data = " "
        result = prime()
        flash("--------- ")
        flash(result[0])
        mathops = result[2]
        count = result[3]
    return render_template('prime.html', name=name, form=form, count=count, mathops = mathops)


@app.route('/nft', methods=['GET', 'POST'])
def nft():
    return render_template('nft.html')



@app.route('/iti', methods=['GET', 'POST'])
def iti():
    form = forms.iti_form()
    room = None
    nights = 0
    pax = 0
    kayak = 0 
    scuba_shore = 0
    scuba_boat = 0
    transfer_hv_pb = 0
    total = 0
    commision = 0
    total_net = 0

    if form.validate_on_submit():
        room = form.room.data
        
        form.room.data = None
      
        nights = form.nights.data
        
        form.nights.data = 0
      
        kayak = form.kayak.data
        
        form.kayak.data = 0
      
        scuba_shore = form.scuba_shore.data
        
        form.scuba_shore.data = 0
      
        scuba_boat = form.scuba_boat.data
        
        form.scuba_boat.data = 0
      
        transfer_hv_pb = form.transfer_hv_pb.data
        
        form.transfer_hv_pb.data = 0

        pax = form.pax.data
        
        form.pax.data = 0

        total_net = (room * nights) + (kayak * pax) + (kayak * pax) + (scuba_shore * pax) + (scuba_boat * pax) + (transfer_hv_pb * pax)
      
 
        total = total_net + (total_net * .25 )
        commision = (total_net * .25)

        flash("")


    return render_template('iti_test.html',
                           total=total,
                           commision=commision,
                           form=form,room=room)
      
