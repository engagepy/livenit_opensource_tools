import requests


def airport_message(airport):

    url = "https://airport-info.p.rapidapi.com/airport"
    airport = str(airport)
    querystring = {"iata": airport}

    headers = {
        "X-RapidAPI-Key": "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7",
        "X-RapidAPI-Host": "airport-info.p.rapidapi.com"
    }

    response = requests.request("GET",
                                url,
                                headers=headers,
                                params=querystring)
    data = response.json()
    print(data)
    return data
