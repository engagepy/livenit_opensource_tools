import requests
import os

def weather(city):
    city = str(city)
  
  #request method for google maps api below
    r2 = requests.get(
        f'https://maps.googleapis.com/maps/api/geocode/json?address={city}, India&key={os.environ["googlemap_key"]}'
    )

  #handling geocode via google maps api here
    r2 = r2.json()
    geo1 = r2['results'][0]['geometry']['location']
    lat_i = geo1['lat']
    lng_i = geo1['lng']
    print("Geocode is ", lat_i, lng_i)

    r = requests.get(
        f"https://api.openweathermap.org/data/3.0/onecall?lat={lat_i}&lon={lng_i}&exclude=hourly,minutely,pressure,uvi,icon,wind_deg&lang=hi&units=metric&appid={os.environ['openweather_key']}"
    )
    r = r.json()

    format = r['current']
    formati = r['timezone']
    format2 = format['temp']
    format3 = format['weather'][0]['description']
    format4 = format['weather'][0]['main']
  
   #print(f'formatted is {format} \n {format2} \n {format3} \n \n \n {formati}')

    data_refined = f'Weather @ {city}.'
  
    data_refined_1 = f'Lat-Long:{lat_i} | {lng_i}' 
  
    data_refined_2 = f'TimeZone : {formati} |'
    data_refined_3 = f'Temp = {format2}°C |'
    data_refined_4 = f'Status = {format4} | in Hindi = {format3}'

    return data_refined, data_refined_1, data_refined_2, data_refined_3, data_refined_4