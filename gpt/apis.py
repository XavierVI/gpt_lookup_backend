from django.conf import settings
import requests
import json
import openai

"""
This function makes a request to Google's geocode API for the postal code
of a POI specified by the user.

Returns the zipcode for the POI or -1 to indicate an error.
"""
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
    else: # response was not 200
        print(f'Google geocode request failed with status code {response.status_code}')
        raise Exception()
    
    return [] # zipcode was not found

"""
This function will fetch 5 zipcodes in a city.
"""
def get_postal_for_city(location):
    headers = {"apikey": settings.ZIPCODEBASE_KEY}
    params = (
    ("city",location['city']),
    ("state_name",location['state']),
    ("country","US"),
    ("limit",5)
    );

    response = requests.get('https://app.zipcodebase.com/api/v1/code/city', headers=headers, params=params);
    if response.status_code == 200:
        data = json.loads(response.text)
        return data
    else:
        print(f'ZIPCODEBASE (city endpoint) responded with status code {response.status_code}')
        raise Exception()


"""
This function fetches zipcodes around the point of interest (POI).
"""
def get_postals_from_radius(postal_code):
    headers = { 
  'apikey': f'{settings.ZIPCODEBASE_KEY}'}

    params = (
    ('code',f'{postal_code}'),
    ('radius','3'), # in km, about 2 miles
    ('country','us'),
    ('limit',5)
    );

    response = requests.get('https://app.zipcodebase.com/api/v1/radius', headers=headers, params=params);
    if response.status_code == 200:
        return response.json()
    else:
        print(f'ZIPCODEBASE (radius endpoint) responded with status code {response.status_code}')
        raise Exception()

"""
This function calls the OpenAI API to generate a JSON object from the user's input.
"""
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
        print('GPT response type: ',type(response))
        print('GPT response: ',response)
        # The response is already a dict, so JsonResponse is unnecessary here
        return response
    except json.JSONDecodeError:
        print("A JSONDecodeError has occurred with GPT's response")
        raise json.JSONDecodeExeption()