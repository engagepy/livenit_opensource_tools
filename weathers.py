import requests
import os
import datetime

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
    print(r)
    format = r['current']
    format_feels = r['current']['feels_like']
    vis = r['current']['visibility']
    wind = r['current']['wind_speed']
    formati = r['timezone']
    format2 = format['temp']
    format3 = format['weather'][0]['description']
    format4 = format['weather'][0]['main']
    moon_phase = r['daily'][0]['moon_phase']
    next_day_feels = r['daily'][0]['feels_like']['day']
    next_day_desc = r['daily'][0]['weather'][0]['main']
    next_day_hindi = r['daily'][0]['weather'][0]['description']
    timestamp = r['current']['dt']
    value = datetime.datetime.fromtimestamp(timestamp)
    print(f"{value:%Y-%m-%d %H:%M:%S}")
    print(moon_phase)
    print(next_day_feels)
    print(next_day_desc)  
    print(next_day_hindi)


  
   #print(f'formatted is {format} \n {format2} \n {format3} \n \n \n {formati}')

    data_refined = f'Weather -> {city}'
    moon_phase_tom = f'Moon Phase = {moon_phase}' 
    data_refined_1 = f'Lat-Long:{lat_i} | {lng_i}' 
    data_feels = f'Feels = {format_feels}°C'
    data_vis = f'Vis = {vis}m'
    data_wind = f'Wind = {wind}'
    data_refined_2 = f'TimeZone : {formati}'
    data_refined_3 = f'Temp = {format2}°C'
    data_refined_4 = f'Status = {format4}, {format3}'

    next_day_feel = f'Tommorrow will feel = {next_day_feels}°C'
    forecast_eng = f'Next Day Forecast = {next_day_desc} | {next_day_hindi}'

    return data_refined,data_refined_3,data_feels,data_vis,data_wind, moon_phase_tom, data_refined_4,next_day_feel,forecast_eng, data_refined_2, data_refined_1