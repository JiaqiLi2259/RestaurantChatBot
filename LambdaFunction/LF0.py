import json
import boto3

def lambda_handler(event, context):
    # TODO implement
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName = 'RestaurantOrderingBot',
        botAlias = 'foodhub',
        userId='Jackie',
        sessionAttributes={
            },
        requestAttributes={
        },
        
        inputText = str(event['message'])
    )
    print("Message from bot:" +response["message"])
    return (response["message"])
    
