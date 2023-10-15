from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
import openai
import json
import requests
from django.conf import settings

def get_gpt_summary(user_prompt):
    # User prompt is already a dict, so json.loads is unnecessary here
    print(user_prompt)
    # At the bottom of the prompt, the text is only accessible using this syntax
    prompt = f"""
    You will be given text from a customer who is looking for a new home, which is delimitted by three backticks. \
    You will pick out specific keywords from the text and use it to create a JSON object. \
    This JSON object will contain two attributes: 'input' which is the location of the house and 'limit' which will always be 5. \
    The format of 'input' should a string in the form: State, City, zipcode. The zipcode is not always necessary.
    
    User text: '''{user_prompt['userIn']}'''
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
    # The response is already a dict, so JsonResponse is unnecessary here
    return response['choices'][0]['message']['content']

@csrf_exempt
def get_listings(request):
    # the text from the request is in request.body
    # json.loads() will turn the request text into a dict
    user_prompt = json.loads(request.body)

    url = "https://realty-in-us.p.rapidapi.com/locations/v2/auto-complete"

    # gpt_res is already a dict
    gpt_res = get_gpt_summary(user_prompt)
    
    print('gpt_res: ',gpt_res)
    querystring = json.loads(gpt_res.content)
    print('Query string: ',querystring)
    
    headers = {
        "X-RapidAPI-Key": settings.RAPID_API_KEY,
        "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    print(response.content)
    # Here we need JsonResponse, text is accessed like request at the top of function
    return JsonResponse(json.loads(response.content), safe=False)