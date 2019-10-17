# Before using this script, you should have installed 'requests'
import sys
import json
import time
import requests

from decimal import Decimal

es_endpoint = 'https://search-steins-gate-ayq3vnqbv3dqhwj62ncd6rmhbe.us-east-2.es.amazonaws.com'
es_index = 'restaurants'
es_type = 'Restaurant'
cuisines = ['Chinese', 'Japanese', 'Korean', 'Italian', 'Indian', 'French']


def read_restaurants(cuisine):
    try:
        with open('yelp_restaurants_data/%s_restaurants_data.json' % cuisine) as json_file:
            res_data = json.load(json_file, parse_float=Decimal)
            print(len(res_data))
            return res_data
    except FileNotFoundError:
        print('Read file failed: ', cuisine)
        return None


def put_data(res_datas, cuisine):
    i = 0
    for res_data in res_datas:
        if not res_data['name'] \
                or not res_data['location']['address1'] \
                or not res_data['location']['city'] \
                or not res_data['location']['state']:
            continue
        payload = dict()
        payload['id'] = res_data['id']
        payload['cuisine'] = cuisine
        url = "%s/%s/%s" % (es_endpoint, es_index, es_type)
        headers = {"Content-Type": "application/json"}
        requests.post(url, data=json.dumps(payload), headers=headers)
        i += 1
        if i % 50 == 0:
            print(i)
    print('Number of data read: ', i)


if __name__ == "__main__":
    for cuisin in cuisines:
        res_datas_to_post = read_restaurants(cuisin)
        if res_datas_to_post:
            put_data(res_datas_to_post, cuisin)
