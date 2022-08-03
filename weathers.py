import requests
import os
import googlemaps




def weather(city):
  #r2 = requests.get(
    #f'https://maps.googleapis.com/maps/api/geocode/json?address=1600+Amphitheatre+Parkway,+Mountain+View,+CA&key={os.environ["googlemap_key"]}')
  gmaps = googlemaps.Client(key=os.environ['googlemap_key'])
  geocode_result = gmaps.geocode(city)
  print(geocode_result)
  r = requests.get(
    f"https://api.openweathermap.org/data/3.0/onecall?lat=33.44&lon=-94.04&exclude=hourly,daily&appid={os.environ['openweather_key']}"
  )
  r = r.json()
  #r2 = r2.json()
  print("R is responding with: :", r)
  #print("R2 is responding with: :", r2)


#  data_refined = f'Temperature °C = {data["temp"]} | Feels Like =
#{data["feels_like"]} | Min = {data["temp_min"]} | Max = {data["temp_max"]} | #Pressure = {data["pressure"]} | Humidity = {data["humidity"]}'

#  print(data_refined)
#  return data_refined
