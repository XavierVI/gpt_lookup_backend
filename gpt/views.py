from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import openai
import json
import requests
from django.conf import settings
import random

@csrf_exempt
def get_listings(request):
    rand_postal = random.randint(0,4)
    postal_code = {}
    data = json.loads(request.body)
    user_prompt = data.get('userIn') # .get retrieves the property
    gpt_res = get_gpt_summary(user_prompt)
    payload = {}
    url = "https://realty-in-us.p.rapidapi.com/properties/v3/list"
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": settings.RAPID_API_KEY,
        "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
    }

    if gpt_res == -1:
        return JsonResponse({'error':'Error: there was an issue parsing GPT response'})
    # You could make things simplier by only calling google maps when POI is defined
    # why else would you use it if the user doesn't specify where exactly they want to live?
    elif gpt_res['POI'] != '':
        postal_code = get_postal_code(gpt_res['location'], gpt_res['POI'])
        print('Google response type: ',type(postal_code))
        print('Google response: ',postal_code)
        if postal_code == -1:
            return JsonResponse({"error": "An error occurred while parsing your request"})
        else:
            postal_code = get_postals_from_radius(postal_code)
            print('Postal type: ',postal_code)
            print('Postal: ',postal_code['results'][rand_postal]['code'])
            payload = {
                "limit": 5,
                "offset": 0,
                "postal_code": postal_code['results'][rand_postal]['code'],
                "status": ["for_sale", "ready_to_build"],
                "sort": {
                    "direction": "desc",
                    "field": "list_date"
                }
            }
    else:
        postal_code = get_postal_for_city(gpt_res['location'])
        payload = {
            "limit": 5,
            "offset": 0,
            "postal_code": postal_code['results'][rand_postal],
            "status": ["for_sale", "ready_to_build"],
            "sort": {
                "direction": "desc",
                "field": "list_date"
            }
        }
        print('Postal for city type: ',type(postal_code))
        print('Postal for city: ',postal_code)
        print(postal_code['results'])
    
    print('Payload type: ',type(payload))
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        listings = response.json()
        print('API response type: ',type(listings))
        print('API response: ',listings)
        return JsonResponse(listings, safe=False)
    else:
        print(response.status_code)
        return JsonResponse({'error':'could not find any matches'})

    # Here we need JsonResponse, text is accessed like request at the top of function
    


# The response from google maps can be quite complex
def get_postal_code(location, poi):
    params = f'address={poi+"+"+location["city"]+"+"+location["state"]}&key={settings.MAPS_KEY}'
    url = f'https://maps.googleapis.com/maps/api/geocode/json?{params}'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print('Google Data type: ',type(data))
        print('Google Data: ',data)
        for comp in data['results'][0]['address_components']:
            for t in comp['types']:
                if t == 'postal_code': return comp['long_name']
    else:
        print(f'Request failed with status code {response.status_code}')
        return -1

def get_postal_for_city(location):
    headers = {"apikey": settings.ZIPCODEBASE_KEY}

    params = (
    ("city",location['city']),
    ("state_name",location['state']),
    ("country","US"),
    ("limit",5)
    );

    response = requests.get('https://app.zipcodebase.com/api/v1/code/city', headers=headers, params=params);
    data = json.loads(response.text)
    return data

def get_postals_from_radius(postal_code):
    headers = { 
  'apikey': f'{settings.ZIPCODEBASE_KEY}'}

    params = (
    ('code',f'{postal_code}'),
    ('radius','5'), # in km
    ('country','us'),
    );

    response = requests.get('https://app.zipcodebase.com/api/v1/radius', headers=headers, params=params);
    print('radius res type: ',type(response.json()))
    print('radius res: ',response.json())
    return response.json()

def get_gpt_summary(user_prompt):
    # User prompt is already a dict, so json.loads is unnecessary here
    print(user_prompt)
    json_form = '{"location":{"city":"...","state":"..."},"POI":"...","postal_code":"...","radius":"25"}'
    # At the bottom of the prompt, the text is only accessible using this syntax
    prompt = f"""
    You will be given text from a customer who is looking for a new home, which is delimitted by three backticks. \
    You will pick out specific keywords from the text and use it to create a JSON object in the following form, delimited by three backticks: \
    '''{json_form}''' \
    This JSON object will contain the attributes: location, POI, postal_code, and radius. \
    The "location" property is where the user wants to live. This property has two other properties "city" and "state". \
    Read the users text and fill in each property. If a city or state isn't listed, set either to be an empty string. \
    Both of the "city" and "state" properties need to be the full name of the city and state and not and not a shortened version of the state's name, in lowercase. \
    For example, instead of returning "state":"ny" return "state":"new york". \
    The "POI" property is simply a point of interest mentioned in the text. If no point of interest is in the text, define this property to be an empty string. \
    The "postal_code" is the postal code the user specified, if none was provided, this property should be -1. \
    The value of the "radius" property is always 25. \
    Always define all properties. If a property value cannot be established from the text, simply make the value an empty string.
    
    User's text: '''{user_prompt}'''
    """
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": prompt
        },
    ],
    temperature=1,
    max_tokens=256,
    stop=None,
    n=1
    )
    try:
        response = json.loads(response['choices'][0]['message']['content'])
    except json.JSONDecodeError:
        return -1
    
    print('GPT response type: ',type(response))
    print('GPT response: ',response)
    # The response is already a dict, so JsonResponse is unnecessary here
    return response