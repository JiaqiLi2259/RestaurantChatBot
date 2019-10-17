import os
import json
import time
import math
import logging
import datetime
import dateutil.parser
import boto3
from botocore.exceptions import ClientError
from botocore.vendored import requests
from urllib.parse import quote

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


SQS_QUEUE_URL = ''; # put your URL
ALL_LOCATIONS = ["manhattan", "brooklyn", "queens", "bronx", "staten island"]
ALL_CUISINES = ["chinese", "french", "italian", "indian", "korean", "japanese"]
MAX_PEOPLE_COUNT = 10
MIN_PEOPLE_COUNT = 1
EST_TIME_ZONE = 'GMT-04:00'
GREETING_FULLFILMENT_Msg = 'Hi there, how can I help?'
THANKYOU_FULLFILMENT_Msg = 'It\'s my honor to help you. Have a good one!'



    
def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False
        
def get_slots(intent_request):
    return intent_request['currentIntent']['slots']
    
def get_session_attributes(intent_request):
    return intent_request['sessionAttributes']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    elicit_slot_response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }
    return elicit_slot_response

def close(session_attributes, fulfillment_state, message):
    close_response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return close_response

def delegate(session_attributes, slots):
    delegate_response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }
    return delegate_response


    
def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
def validate_paras(dining_location, dining_cuisine, dining_date, dining_time, dining_people, phone_number):
    if dining_location is not None and dining_location.lower() not in ALL_LOCATIONS:
        return build_validation_result(False,
                                       'DiningLocation',
                                       'We do not have restaurants in {} area, would you like a different location of restaurant? Our most popular location is Manhattan'.format(dining_location))
    if dining_cuisine is not None and dining_cuisine.lower() not in ALL_CUISINES:
        return build_validation_result(False,
                                       'DiningCuisine',
                                       'We do not have restaurants in {} style, would you like a different style of food? Our most popular cuisine is Chinese'.format(dining_cuisine))
    if dining_date is not None:
        if not isvalid_date(dining_date):
            return build_validation_result(False, 
                                           'DiningDate', 
                                           'It\'s not a valid date. I did not understand that, what date would you like?')
        elif datetime.datetime.strptime(dining_date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 
                                           'DiningDate', 
                                           'You can\'t make a reservation from past. What day in the future would you like to choose?')
    if dining_time is not None:
        if len(dining_time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)
        hour, minute = dining_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', None)
        if datetime.datetime.strptime(dining_date, '%Y-%m-%d').date() == datetime.date.today():
            localtime = time.localtime(time.time())
            localhour = parse_int(localtime.tm_hour)
            localminute = parse_int(localtime.tm_min)
            if hour < localhour or (hour == localhour and minute < localminute):
                return build_validation_result(False, 
                                               'DiningTime', 
                                               'You can\'t make a reservation from past. What time in the future would you like to choose?')
        if hour < 10 or hour > 22:
            # Outside of business hours
            return build_validation_result(False, 
                                           'DiningTime', 
                                           'Our business hours are from ten a m. to ten p m. Can you specify a time during this range?')
    
    if dining_people is not None:
        number_of_people = parse_int(dining_people)
        if math.isnan(number_of_people):
            return build_validation_result(False, 'DiningPeople', None)
        if number_of_people < MIN_PEOPLE_COUNT or number_of_people > MAX_PEOPLE_COUNT:
            return build_validation_result(False,
                                           'DiningPeople',
                                           'Sorry, the number of people you provide should between 1 and 10. Can you specify a number during this range?')
    if phone_number is not None:
        length_of_digit = len(phone_number)
        if length_of_digit != 10:
            return build_validation_result(False,
                                           'PhoneNumber',
                                           'Sorry, we only support American phone number. Can you give us your US phone number in ten digits?')
                                           
    return build_validation_result(True, None, None)
    
def handleDialogHook(intent_request):
    dining_location = get_slots(intent_request)["DiningLocation"]
    dining_cuisine = get_slots(intent_request)["DiningCuisine"]
    dining_date = get_slots(intent_request)["DiningDate"]
    dining_time = get_slots(intent_request)["DiningTime"]
    dining_people = get_slots(intent_request)['DiningPeople']
    phone_number = get_slots(intent_request)['PhoneNumber']

    slots = get_slots(intent_request)
    validation_result = validate_paras(dining_location, dining_cuisine, dining_date, dining_time, dining_people, phone_number)
    if not validation_result['isValid']:
    # param that users give is illegal, try to obtain data again
        slots[validation_result['violatedSlot']] = None
        return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
    else:
        return delegate(intent_request['sessionAttributes'], slots)
    
def send_sqs_message(sqs_queue_url, msg_body):
    """
    :param sqs_queue_url: String URL of existing SQS queue
    :param msg_body: String message body
    :return: Dictionary containing information about the sent message. If error, returns None.
    """
    # Send the SQS message
    sqs_client = boto3.client('sqs')
    try:
        msg = sqs_client.send_message(QueueUrl=sqs_queue_url,
                                      MessageBody=msg_body)
    except ClientError as e:
        logging.error(e)
        return None
    return msg
    
def handleFulfillmentHook(intent_request):
    slots = get_slots(intent_request)
    fullFilmentMsg = 'Thanks for all your information! I will notify you over SMS once I have the list of restaurant suggestions.'
    dining_location = slots["DiningLocation"]
    dining_cuisine = slots["DiningCuisine"]
    dining_date = slots["DiningDate"]
    dining_time = slots["DiningTime"]
    dining_people = slots['DiningPeople']
    phone_number = slots['PhoneNumber']
    print(dining_location, dining_cuisine, dining_date, dining_time, dining_people, phone_number)
    
    # Send message to SQS queue
    # supported 'DataType': string, number, binary
    msg_body = {
        'location': {
            'DataType': 'String',
            'StringValue': dining_location
        },
        'cuisine': {
            'DataType': 'String',
            'StringValue': dining_cuisine
        },
        'date': {
            'DataType': 'String',
            'StringValue': dining_date
        },
        'time': {
            'DataType': 'String',
            'StringValue': dining_time
        },
        'people': {
            'DataType': 'Number',
            'StringValue': str(dining_people)
        },
        'phone': {
            'DataType': 'String',
            'StringValue': str(phone_number)
        }
    }
    msg_body = str(msg_body)
    send_message = send_sqs_message(SQS_QUEUE_URL, msg_body)
    if send_message is not None:
        print('Sent SQS message: '+ str(send_message))
    else:
        print('Sent data FAILED!')
    return close(intent_request['sessionAttributes'], 'Fulfilled', { 'contentType' : 'PlainText', 'content' : fullFilmentMsg });

def dining_suggestions_handler(intent_request):
    """
    Performs dialog management and fulfillment for ordering flowers.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action in slot validation and re-prompting.
    """
    
    source = intent_request['invocationSource']
    
    if source == 'DialogCodeHook':
    # Perform basic validation on the supplied input slots.
    # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        return handleDialogHook(intent_request)
    elif source == 'FulfillmentCodeHook':
        return handleFulfillmentHook(intent_request)
    else:
        raise Exception('Source with name ' + source + ' not supported')
        
def greeting_handler(session_attributes):
    return close(session_attributes, 'Fulfilled', { 'contentType' : 'PlainText', 'content' : GREETING_FULLFILMENT_Msg })
    
def thankyou_handler(session_attributes):
    return close(session_attributes, 'Fulfilled', { 'contentType' : 'PlainText', 'content' : THANKYOU_FULLFILMENT_Msg })
                
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']
    # Dispatch to your bot's diffrent intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggestions_handler(intent_request)
    elif intent_name == 'GreetingIntent':
        session_attributes =  get_session_attributes(intent_request)
        return greeting_handler(session_attributes)
    elif intent_name == 'ThankYouIntent':
        session_attributes =  get_session_attributes(intent_request)
        return thankyou_handler(session_attributes)
    else:
        raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    """
              --- Main handler ---
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
