import requests


def superhero(s):
  url = "https://superhero-search.p.rapidapi.com/api/"
  s = str(s)
  querystring = {"hero":s}
  
  headers = {
  	"X-RapidAPI-Key": "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7",
  	"X-RapidAPI-Host": "superhero-search.p.rapidapi.com"
  }
  
  response = requests.request("GET", url, headers=headers, params=querystring)
  
  return response.json()