# Lookup Demo
This is a demo created to showcase the potential of LLMs in helping realtors find homes for customers.
This repo is the backend for the full demo, and uses several APIs to turn the user's request into
a json object which can be used to find homes relevant to their request.

# How it works
This django application contains a single view that calls several other functions to parse the request and fetch the user's results.
The APIs used in this project are the OpenAI API, Google Geocode API, ZIPCODEBASE API, and ... on RapidAPI.

## OpenAI API
ChatGPT is used to turn the user's request into a JSON object. Prompt engineering was used
to help guarantee ChatGPT's response is consistent and always aligns with the chosen structure of the JSON object.

## Google Geocode API
This API is used to fetch the zipcode of the user's specified point of interest.
If none was provided (detected by ChatGPT), then this is never used.

## ZIPCODEBASE
This is an API that can retrieve zipcodes in the US based on radius or geographic location.
If the user specified a point of interest and the zipcode was retrieved by Google's Geocode API,
then other zipcodes within a 2 mile radius are retieved.

This can also be used to get some general zipcodes in a city.

## Rapid API
The Reality in US API on RapidAPI (https://rapidapi.com/apidojo/api/realty-in-us/) is used to fetch houses using the retrieved zipcodes.
