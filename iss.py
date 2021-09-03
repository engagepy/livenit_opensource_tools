import os
from twilio.rest import Client
import requests
cred_token = os.environ['token']
cred_id = os.environ['id']
account_sid = cred_id
auth_token = cred_token
client = Client(account_sid, auth_token)

people = requests.get('http://api.open-notify.org/astros.json')
dic = people.json()
names = dic['people']
namez = " "
for i in names:
  namez += str(i['name'])
  namez += ", "
    
iss_loc = requests.get('http://api.open-notify.org//iss-now.json')    
loc = iss_loc.json()
position = loc['iss_position']
lat = str(position['latitude'])
long = str(position['longitude'])
 

def message():
  mes = 'Humans in space right now = ' + str(dic['number']) + "." + ' Their names: ' + namez + ' ISS Location: Lat {}, Long {} '.format(lat,long)
  return mes
#formulate the message that will be sent
'''
message_c = client.messages.create(
to= "+919818933350",
from_="+18647272921",
body=mes)   
sent_ids = [message_c.sid]
print(sent_ids)'''