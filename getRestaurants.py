import requests
import json
from yelpApi import get_key

API_KEY = get_key()
ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
HEADERS = {'Authorization':'bearer %s' %API_KEY}
OFFSET = -50

with open('restaurants_data4.json', 'w') as outfile:
    outfile.write('[')
    for _ in range(2):
        OFFSET += 50
        PARAMETERS = {
            'term': 'Chinese restaurant',
            'limit': 50,
            'offset': OFFSET,
            'location': 'Manhattan'
        }
        # Make a request to the Yelp API
        response = requests.get(url=ENDPOINT, params=PARAMETERS, headers=HEADERS)

        # Convert the JSON string to dictionary
        business_data = response.json()

        # print the response
        print(business_data['total'])
        # print (business_data.keys())
        for data in business_data['businesses']:
            json.dump(data, outfile, indent=4)
            outfile.write(',')
    outfile.write(']')