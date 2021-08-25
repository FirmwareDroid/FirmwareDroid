# API references from https://github.com/ozguralp/gmapsapiscanner
# License available at: https://github.com/ozguralp/gmapsapiscanner/blob/master/LICENSE
import logging


GOOGLE_MAP_LINKS_DICT = {
	"Customsearch": ["https://www.googleapis.com/customsearch/v1?cx=017576662512468239146:omuauf_lfve&q=lectures&key="],
	"Staticmap": ["https://maps.googleapis.com/maps/api/staticmap?center=45%2C10&zoom=7&size=400x400&key="],
	"Streetview": ["https://maps.googleapis.com/maps/api/streetview?size=400x400&location=40.720032,-73.988354&fov=90&heading=235&pitch=10&key="],
	"Embed (Basic)": ["https://www.google.com/maps/embed/v1/place?q=Seattle&key="],
	"Embed (Advanced)": ["https://www.google.com/maps/embed/v1/search?q=record+stores+in+Seattle&key="],
	"Directions & Directions (Advanced)": ["https://maps.googleapis.com/maps/api/directions/json?origin=Disneyland&destination=Universal+Studios+Hollywood4&key="],
	"Geocode": ["https://maps.googleapis.com/maps/api/geocode/json?latlng=40,30&key="],
	"Distance Matrix & Distance Matrix (Advanced)": ["https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=40.6655101,-73.89188969999998&destinations=40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.6905615%2C-73.9976592%7C40.659569%2C-73.933783%7C40.729029%2C-73.851524%7C40.6860072%2C-73.6334271%7C40.598566%2C-73.7527626%7C40.659569%2C-73.933783%7C40.729029%2C-73.851524%7C40.6860072%2C-73.6334271%7C40.598566%2C-73.7527626&key="],
	"Find Place From Text": ["https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=Museum%20of%20Contemporary%20Art%20Australia&inputtype=textquery&fields=photos,formatted_address,name,rating,opening_hours,geometry&key="],
	"Autocomplete & Autocomplete Per Session": ["https://maps.googleapis.com/maps/api/place/autocomplete/json?input=Bingh&types=%28cities%29&key="],
	"Elevation": ["https://maps.googleapis.com/maps/api/elevation/json?locations=39.7391536,-104.9847034&key="],
	"Timezone": ["https://maps.googleapis.com/maps/api/timezone/json?location=39.6034810,-119.6822510&timestamp=1331161200&key="],
	"Nearest Roads": ["https://roads.googleapis.com/v1/nearestRoads?points=60.170880,24.942795|60.170879,24.942796|60.170877,24.942796&key="],
	"Geolocation": ["https://www.googleapis.com/geolocation/v1/geolocate?key="],
	"Route to Traveled": ["https://roads.googleapis.com/v1/snapToRoads?path=-35.27801,149.12958|-35.28032,149.12907&interpolate=true&key="],
	"Speed Limit-Roads": ["https://roads.googleapis.com/v1/speedLimits?path=38.75807927603043,-9.03741754643809&key="],
	"Place Details": ["https://maps.googleapis.com/maps/api/place/details/json?place_id=ChIJN1t_tDeuEmsRUsoyG83frY4&fields=name,rating,formatted_phone_number&key="],
	"Nearby Search-Places": ["https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522,151.1957362&radius=100&types=food&name=harbour&key="],
	"Text Search-Places": ["https://maps.googleapis.com/maps/api/place/textsearch/json?query=restaurants+in+Sydney&key="],
	"Places Photo": ["https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference=CnRtAAAATLZNl354RwP_9UKbQ_5Psy40texXePv4oAlgP4qNEkdIrkyse7rPXYGd9D_Uj1rVsQdWT4oRz4QrYAJNpFX7rzqqMlZw2h2E2y5IKMUZ7ouD_SlcHxYq1yL4KbKUv3qtWgTK0A6QbGh87GB3sscrHRIQiG2RrmU_jF4tENr9wGS_YxoUSSDrYjWmrNfeEHSGSc3FyhNLlBU&key="],
	"Playable Locations": ["https://playablelocations.googleapis.com/v3:samplePlayableLocations?key="],
	"FCM Takeover": ["https://fcm.googleapis.com/fcm/send"],
}

REQUEST_DATA = {"Geolocation": {'considerIp': 'true'},
				"Playable Locations": {'area_filter': {'s2_cell_id': 7715420662885515264}, 'criteria': [{'gameObjectType': 1, 'filter': {'maxLocationCount': 4, 'includedTypes': ['food_and_drink']},'fields_to_return': {'paths': ['name']}}, {'gameObjectType': 2, 'filter': {'maxLocationCount': 4},'fields_to_return': {'paths': ['types', 'snapped_point']}}]},
				"FCM Takeover": "{'registration_ids':['ABC']}"}


def verifiy_google_map_endpoints(apikey):
	"""
	Verifies if the api key works with the google maps API.
	:param apikey: str - Google API key
	:return: dict(str, list(str) = dict(API-Name, list(PoC-links))
	"""
	import requests
	result_dict = {}
	logging.info(f"Test api-key: {apikey}")
	for api_name, link_list in GOOGLE_MAP_LINKS_DICT.items():
		request_data = None
		headers = None
		if api_name in REQUEST_DATA.keys():
			request_data = REQUEST_DATA[api_name]
			if api_name == "FCM Takeover":
				headers = {'Content-Type': 'application/json', 'Authorization': 'key='+apikey}
		for link in link_list:
			url = str(link)+str(apikey)
			try:
				response = requests.get(url, verify=True, data=request_data, headers=headers)
				if response.status_code == 200 and response.text.find("error") < 0:
					logging.info(f"Valid API Key found {api_name} - PoC-Link: {url}")
					if api_name not in result_dict:
						result_dict[api_name] = [url]
					else:
						result_dict[api_name].append(url)
				else:
					logging.info(f"Invalid API Key found for {api_name}")
			except Exception as err:
				logging.info(f"Endpoint exception: {link} error: {err}")
	return result_dict
