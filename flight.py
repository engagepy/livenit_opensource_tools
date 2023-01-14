import requests
def flight_message(arrival, departure):
	url = f"https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com/apiservices/browsequotes/v1.0/IN/INR/en-US/{departure}-sky/{arrival}-sky/anytime"

	querystring = {
    "inboundpartialdate": "2019-12-01"
    }

	headers = {
	    'x-rapidapi-key': "ca396c8c62mshf51f177a6611b4ap1cf15ajsnb909632c0ce7",
	    'x-rapidapi-host':
	    "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
	}
	response = requests.request("GET",
	                            url,
	                            headers=headers,
	                            params=querystring)

	dic = response.json()

	print(dic)
	data = dic['Quotes']
	print(data)
	min_prices = " "
	dates = " "
	for i in data:
		min_prices += str(i["MinPrice"])
		min_prices += " | "
		bad_formate_date = i["OutboundLeg"]["DepartureDate"]
		good_date = bad_formate_date[0:10]
		dates += good_date + " | "

	print(min_prices)
	print(dates)
	#mes1 = f"Prices in INR: {min_prices}"
	#mes2 = f"Corresponding Dates: {dates}"
	return mes1, mes2