from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import openai
import json
import requests
from django.conf import settings

instruction = "You are analyzing text gathered from a customer who is looking for a new home. \
    You will pick out specific keywords from the text and use it to form a JSON object which matches what the customer is looking for. \
    Your response will always be a JSON object. \
    The format of your response will be: <\{\"input\":\"\<location>\", \"limit\": \"5\"\}> \
    where <location> will be a string of the state, city, and zipcode of the area the customer \
    wants to move to. The state and city must be specified but the zipcode is optional. The \"limit\" property is always 5.\n"

def get_gpt_summary(user_prompt):
    prompt = repr("<{user_prompt.userIn}>")
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": instruction + prompt
        }
    ],
    temperature=1,
    max_tokens=256,
    stop=None,
    n=1
    )
    print(response.choices[0].message.content)
    return JsonResponse(response['choices'][0]['message']['content'], safe=False)

@csrf_exempt
def get_listings(request):
    user_prompt = json.loads(request.body)

    url = "https://realty-in-us.p.rapidapi.com/locations/v2/auto-complete"

    querystring = json.loads(get_gpt_summary(user_prompt))
    
    print(json.loads(querystring.content))
    headers = {
        "X-RapidAPI-Key": settings.RAPID_API_KEY,
        "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    print(response.json())
    return JsonResponse(response.json(), safe=False)