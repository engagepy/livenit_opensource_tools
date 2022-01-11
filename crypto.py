

def coin():

  import requests

  url = "https://bravenewcoin.p.rapidapi.com/oauth/token"

  payload = "{\r\"audience\": \"https://api.bravenewcoin.com\",\r\"client_id\": \"oCdQoZoI96ERE9HY3sQ7JmbACfBf55RY\",\r\"grant_type\": \"client_credentials\"\r}"
  headers = {
    'content-type': "application/json",
    'x-rapidapi-host': "bravenewcoin.p.rapidapi.com",
    'x-rapidapi-key': "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7"
    }

  response = requests.request(
            "POST", url, data=payload, 
            headers=headers)
  datas = response.json()
  token = datas['access_token']


  #print(response.text)

  url = "https://bravenewcoin.p.rapidapi.com/market-cap"
  querystring = {
    "assetId":" f1ff77b6-3ab4-4719-9ded-2fc7e71cff1f"
    }
  headers = {
        'authorization': f"Bearer {token}",
        'x-rapidapi-host': "bravenewcoin.p.rapidapi.com",
        'x-rapidapi-key': "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7"
        }
  response = requests.request(
            "GET", url, headers=headers, 
            params=querystring)
  dic = response.json()
  ##print(dic)
 
  data = dic['content']
  price = data[0]['price']
  marketcaprank = data[0]['marketCapRank']
  volume = data[0]['volume']
  totalsupply = data[0]['totalSupply']
  timestamp = data[0]['timestamp']
  #print(data)
  mes1 = f"BTC Market Capital Rank is {marketcaprank}."  
  mes2 = f"BTC in $ = {price} per/btc."
  mes3 = f"Market Volume = {volume}."
  mes4 = f"Total Supply Mined of 21 Million Max Coins = {totalsupply}."
  mes5 = f" "
  mes6 = f"Data fetched on {timestamp}"


  print(mes1, mes2,mes3,mes4,mes5,mes6)

  return mes1, mes2, mes3, mes4, mes5, mes6