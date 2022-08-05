import requests
import os
import googlemaps


def weather(lat, lon):
    r2 = requests.get(
        f'https://maps.googleapis.com/maps/api/geocode/json?address=Port+Blair, India&key={os.environ["googlemap_key"]}'
    )
    #gmaps = googlemaps.Client(key=os.environ['googlemap_key'])
    #geocode_result = gmaps.geocode(city)
    #print(geocode_result)
    r = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&exclude=hourly,minutely,pressure,uvi,icon,wind_deg&lang=hi&units=metric&appid={os.environ['openweather_key']}"
    )
    r = r.json()
    r2 = r2.json()
    print(r2)
  
    format = r['current']
    formati = r['timezone']
    format2 = format['temp']
    format3 = format['weather'][0]['description']
    format4 = format['weather'][0]['main']
    print(f'formatted is {format} \n {format2} \n {format3} \n \n \n {formati}')


    data_refined = f'Weather @ Latitude: {lat} & Longitude: {lon} in TimeZone : {formati} ||\n Temp = {format2}°C | \n Status = {format4} |\n Hindi = {format3}'
    data_refined = str(data_refined)
    #print(data_refined)
    return data_refined