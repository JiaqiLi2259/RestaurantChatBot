from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from random import randrange
import boto3
import json

host = '' # put your host
region = '' # put your region

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, \
                   region, service, session_token=credentials.token)

# print(credentials.access_key, credentials.secret_key)

es_endpoint = '' # put your endpoint
es_index = 'restaurants'
es_type = 'Restaurant'

es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

dynamodb = boto3.resource('dynamodb')


def get_rand_from_es(cuisine):
    count_resp = es.search(index=es_index,
                           body={
                               "query":
                                   {"bool":
                                       {"must": [
                                           {"match": {"cuisine": cuisine}},
                                           {"match": {"_type": es_type}}
                                       ]}
                                   }
                           }
                           )
    result_count = count_resp['hits']['total']['value']

    searched = es.search(index=es_index,
                         body={
                             "query":
                                 {"bool":
                                     {"must": [
                                         {"match": {"cuisine": cuisine}},
                                         {"match": {"_type": es_type}}
                                     ]}
                                 },
                             "size": 3,
                             "from": randrange(result_count)
                         }
                         )
    results = searched['hits']['hits']
   

    return results


def get_full_restaruant_info(ddb_bizId):
    table = dynamodb.Table('yelp-restaurants')
    response = table.get_item(
        Key={
            'bizId': ddb_bizId
        }
    )
    item = response['Item']
    return item


def get_suggestion(cuisine):
    results = get_rand_from_es(cuisine)
    items = []
    for result in results:
        items.append(get_full_restaruant_info(result['_source']['id']))

    return items
