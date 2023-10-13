from django.shortcuts import render
from django.http import JsonResponse
import openai
import requests
from django.conf import settings

ins1 = "You are an assistant for a realitor that summarizes text from a home buyer."
ins2 = "You will be provided with text that details what kind of home a user is looking for."
ins3 = "Look for key words from the text and return your response as a JSON object that contains the attributes for the home the user wants."
instruction = ins1+ins2+ins3

user_prompt = "I'm looking for a home near UNM for my three kids, has a big garage and backyard."

def get_gpt_summary(request):
    response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
        "role": "system",
        "content": instruction + repr("<{user_prompt}>")
        }
    ],
    temperature=1,
    max_tokens=256,
    stop=None,
    n=1
    )
    print(response.choices[0].message.content)
    return JsonResponse(response['choices'][0]['message']['content'], safe=False)

def get_listings(request):
    json = get_gpt_summary()

    url = "https://realty-in-us.p.rapidapi.com/locations/v2/auto-complete"

    querystring = {"input":"new york","limit":"5"}

    headers = {
        "X-RapidAPI-Key": settings.RAPID_API_KEY,
        "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    print(response.json())
    return JsonResponse(response.json(), safe=False)