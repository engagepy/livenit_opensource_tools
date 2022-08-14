import datetime
import requests

def coin(symbol):
    
    
    # Get Token Valid for 24 Hours
    url = "https://bravenewcoin.p.rapidapi.com/oauth/token"

    payload = "{\r\"audience\": \"https://api.bravenewcoin.com\",\r\"client_id\": \"oCdQoZoI96ERE9HY3sQ7JmbACfBf55RY\",\r\"grant_type\": \"client_credentials\"\r}"
    headers = {
        'content-type': "application/json",
        'x-rapidapi-host': "bravenewcoin.p.rapidapi.com",
        'x-rapidapi-key': "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7"
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    datas = response.json()
    token = datas['access_token']

    #Get Asset ID by Symbol
    url = "https://bravenewcoin.p.rapidapi.com/asset"

    querystring = {"symbol":f"{symbol.upper()}","status":"ACTIVE"}

    headers = {
	    "X-RapidAPI-Key": "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7",
	    "X-RapidAPI-Host": "bravenewcoin.p.rapidapi.com"
    }

    response_id = requests.request("GET", url, headers=headers, params=querystring)
    dic_id = response_id.json()
    data_keys = dic_id['content']
    data_id = str(data_keys[0]['id'])
    data_name = data_keys[0]['name']
  

    # Get the asset details
  
    url = "https://bravenewcoin.p.rapidapi.com/market-cap"
    querystring = {"assetId": f" {data_id}"}
    headers = {
        'authorization': f"Bearer {token}",
        'x-rapidapi-host': "bravenewcoin.p.rapidapi.com",
        'x-rapidapi-key': "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7"
    }
    response = requests.request("GET",
                                url,
                                headers=headers,
                                params=querystring)
    dic = response.json()
    #print(dic)
    data = dic['content']
    price = str(data[0]['price'])
    marketcaprank = data[0]['marketCapRank']
    total_market_cap = str(data[0]['totalMarketCap'])

    totalsupply = data[0]['totalSupply']
    timestamp = data[0]['timestamp']
    mes1 = f"{data_name} Mkt Rank {marketcaprank}"
    mes2 = f"Price = {price[0:9]}$ per/{symbol}"
    mes3 = f"Mkt Cap = {total_market_cap[0:20]}$"
    mes4 = f"Supply = {totalsupply}"
    mes5 = f" "
    mes6 = f"Timestamp: {timestamp[:19]} GMT"
    #print(mes1, mes2, mes3, mes4, mes5, mes6)
  
    return mes1, mes2, mes3, mes4, mes5, mes6
