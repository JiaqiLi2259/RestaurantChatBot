import restaurant_suggest
import json
import boto3
import logging
from botocore.vendored import requests
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

# LF2 as a queue worker
# Whenever it is invoked by the CloudWatch event trigger that runs every minute:
# 1. pulls a message from the SQS queue,
# 2. gets a random restaurant recommendation for the cuisine collected through conversation from ElasticSearch and DynamoDB,
# 3. formats them and
# 4. sends them over text message to the phone number included in the SQS message, using SNS
# choose the elasticsearch index: "restaurants" is the easier version, "predictions" is with the ML service

SQS_QUEUE_URL = '' # put your URL
ES_HOST = '' # put your host
ES_INDEX = 'restaurants'
ES_TYPE = 'Restaurant'


def receive_sqs_message(sqs_queue_url):
    # Receive the SQS message
    sqs_client = boto3.client('sqs')
    try:
        response = sqs_client.receive_message(
            QueueUrl=sqs_queue_url,
            AttributeNames=[
                'All'
            ],
            MessageAttributeNames=[
                'All'
            ],
            MaxNumberOfMessages=1,
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )
    except ClientError as e:
        logging.error(e)
        return None
    return response


def delete_sqs_message(sqs_queue_url, receipt_handle):
    # Delete the SQS message
    sqs_client = boto3.client('sqs')
    try:
        sqs_client.delete_message(
            QueueUrl=sqs_queue_url,
            ReceiptHandle=receipt_handle
        )
    except ClientError as e:
        #logging.error(e)
        print(e)
        return False
    return True


def lambda_handler(event, context):
    # TODO implement
    print("Testing CloudWatch: Call LF2 every minute.")

    # Receive a message from SQS queue
    response = receive_sqs_message(SQS_QUEUE_URL)
    while not ('Messages' in response):
        response = receive_sqs_message(SQS_QUEUE_URL)
    if response is not None:
        receipt_handle = response['Messages'][0]['ReceiptHandle']
        # Delete a message from SQS queue
        delete_flag = True
        delete_flag = delete_sqs_message(SQS_QUEUE_URL, receipt_handle)
        if delete_flag:
            # all information stored in sqs queue
            message = response['Messages'][0]['Body']
            message = message.replace("\'", '"')
            message = json.loads(message)
            location = message['location']['StringValue']
            cuisine = message['cuisine']['StringValue']
            dining_date = message['date']['StringValue']
            dining_time = message['time']['StringValue']
            number_of_people = message['people']['StringValue']
            phone_number = message['phone']['StringValue']
            phone_number = '+1'+str(phone_number)
            print(location, cuisine, dining_date, dining_time, number_of_people, phone_number)
            item = restaurant_suggest.get_suggestion(cuisine)
            name_list = []
            rest_dic = []
            for i in range(3):
                name_list.append(item[i]['name'])
                rest_dic.append(item[i]['address'])
            reservation = 'Hello! Here are my {} restaurant suggestions for {} people, on {}, {} at {}: (1). {} located at {} (2). {} located at {} (3). {} located at {}. Enjoy your meal!'.format(
                cuisine, number_of_people, dining_date, dining_time, location, name_list[0], rest_dic[0],
                name_list[1], rest_dic[1], name_list[2], rest_dic[2])
            print(reservation)
            # Create an SNS client
            client = boto3.client("sns")
            # Send your sms message.
            client.publish(
                PhoneNumber=phone_number,
                Message=reservation
            )
        else:
            print('Delete messages Error!')
    else:
        print('Receive messages Error!')
    return delete_flag


