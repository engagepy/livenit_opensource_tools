import requests
def weather(city):
  url = "https://community-open-weather-map.p.rapidapi.com/find"

  querystring = {
    "q":f"{city}","cnt":"1","mode":"html","lon":"0","type":"accurate","lat":"0","units":"metric"
    }

  headers = {
    'x-rapidapi-host': "community-open-weather-map.p.rapidapi.com",
    'x-rapidapi-key': "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7"
    }

  response = requests.request(
            "GET", url, headers=headers, 
            params=querystring)
  dic = response.json()
  print(dic)
  data = dic['list']
  data = data[0]['main']
  print(data)
  data_refined = f'Temperature °C = {data["temp"]} | Feels Like = {data["feels_like"]} | Min = {data["temp_min"]} | Max = {data["temp_max"]} | Pressure = {data["pressure"]} | Humidity = {data["humidity"]}' 

  print(data_refined)
  return data_refined