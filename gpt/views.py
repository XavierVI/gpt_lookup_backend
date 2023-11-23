from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import json
import requests
from django.conf import settings
import random
from apis import *

@csrf_exempt
def get_listings(request):
    try:
        rand_postal = random.randint(0,4)
        postal_code = {}
        data = json.loads(request.body)
        user_prompt = data.get('userIn') # .get retrieves the property
        payload = {}
        url = "https://realty-in-us.p.rapidapi.com/properties/v3/list"
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": settings.RAPID_API_KEY,
            "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
        }
        houses = []
        gpt_res = get_gpt_summary(user_prompt)

        # If user specified a POI, call Google geocode API to get the POI's postal code
        # then use zipcode base to gather postal codes around the POI
        if gpt_res['POI'] != '':
            postal_code = get_postal_code(gpt_res['location'], gpt_res['POI'])
            print('Google response type: ',type(postal_code))
            print('Google response: ',postal_code)
            postal_code = get_postals_from_radius(postal_code)
            print('Postal type: ',postal_code)
            print('Postal: ',postal_code['results'][rand_postal]['code'])
            for postal_code in postal_code['results']:
                payload = {
                    "limit": 5,
                    "offset": 0,
                    "postal_code": postal_code['code'],
                    "status": ["for_sale", "ready_to_build"],
                    "sort": {
                        "direction": "desc",
                        "field": "list_date"
                    }
                }
                # rapid API request
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    houses.append(response.json())
                else:
                    print(response.status_code)
        
        # fetches postal codes for the city
        else:
            postal_code = get_postal_for_city(gpt_res['location'])
            for postal_code in postal_code['results']:
                payload = {
                    "limit": 5,
                    "offset": 0,
                    "postal_code": postal_code,
                    "status": ["for_sale", "ready_to_build"],
                    "sort": {
                        "direction": "desc",
                        "field": "list_date"
                    }
                }
                # rapid API request
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    houses.append(response.json())
                else:
                    print(response.status_code)

        return JsonResponse(houses, safe=False)
    # catches any exceptions 
    except Exception:
        print("Error occurred in get_listings")
        print(Exception)
        return HttpResponse(status=500)
