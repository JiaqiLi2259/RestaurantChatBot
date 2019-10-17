import sys
import json
import time

import boto3
from decimal import Decimal

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


def put_ddb(restaruants_objs):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('yelp-restaurants')
    i = 0
    response = None
    for restaruants_obj in restaruants_objs:
        try:
            if not restaruants_obj['name']\
                    or not restaruants_obj['location']['address1']\
                    or not restaruants_obj['location']['city']\
                    or not restaruants_obj['location']['state']:
                continue
            i += 1
            if i % 50 == 0:
                print(i)
            res_item = dict()
            res_item['bizId'] = restaruants_obj['id']
            res_item['name'] = restaruants_obj['name']
            res_item['insertedAtTimestamp'] = int(time.time())
            res_item['address'] = restaruants_obj['location']['address1']
            res_item['city'] = restaruants_obj['location']['city']
            res_item['state'] = restaruants_obj['location']['state']
            res_item['coordinates'] = restaruants_obj['coordinates']
            res_item['reviewCount'] = restaruants_obj['review_count']
            res_item['rating'] = Decimal(restaruants_obj['rating'])
            if restaruants_obj['location']['zip_code']:
                res_item['zipCode'] = restaruants_obj['location']['zip_code']
            response = table.put_item(
                Item=res_item
            )
        except Exception:
            print(restaruants_obj)

    print("PutItem %s succeeded: " % cuisine)
    print("Number of items: %s" % i)
    print(json.dumps(response))


if __name__ == "__main__":
    for cuisine in cuisines:
        res_datas = read_restaurants(cuisine)
        if res_datas:
            print("Start uploading cuisine: %s" % cuisine)
            put_ddb(res_datas)
