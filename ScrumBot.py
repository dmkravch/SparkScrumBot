#!/usr/bin/python2.7
import logging
#import smartsheet
import sys, json, requests
from flask import Flask, request
import datetime
#needed for the topic search
import requests
import apiai
import pymongo
#for random choice in topic search
from ciscosparkapi import CiscoSparkAPI, Webhook
i=0
logging.basicConfig(filename='LogScrumBot.log',level=logging.DEBUG,format='%(asctime)s %(message)s')
app = Flask(__name__)

accesstoken="ZTE4MWNiNTktNGVmNS00MWVmLTg3NzAtZWM1ZDU1OTY0ODkyOTE4MDBjOTEtMWYy"
spark_api = CiscoSparkAPI(accesstoken)
accesstoken="Bearer "+accesstoken
#The main space ID with all the users in question
roomID='Y2lzY29zcGFyazovL3VzL1JPT00vODZjYzg4NzAtNjdjYy0xMWU3LTgxZTYtYzM1MDA1YTVkZTFj'
# Client Access Token for accessing our API AI Bot
CLIENT_ACCESS_TOKEN = 'af585a7d41ac4fc5a8174a6cd7cd6651'
ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)
response_message = []

def _url(path):
    a = 'https://api.ciscospark.com/v1' + path
    return a

def get_message(at,messageId):
    headers = {'Authorization':at}
    #resp = requests.get(_url('/messages/{:s}'.format(messageId)),headers=headers)
    resp = requests.get(_url('/messages/{0}'.format(messageId)),headers=headers)
    dict = json.loads(resp.text)
    dict['statuscode']=str(resp.status_code)
    return dict

def post_message(at,roomId,text):
    headers = {'Authorization':at, 'content-type':'application/json'}
    payload = {'roomId':roomId, 'text':text}
    resp = requests.post(url=_url('/messages'),json=payload, headers=headers)
    dict = json.loads(resp.text)
    dict['statuscode']=str(resp.status_code)
    return dict

def post_message_based_on_email(at,toPersonEmail,text):
    headers = {'Authorization':at, 'content-type':'application/json'}
    payload = {'toPersonEmail':toPersonEmail, 'text':text}
    resp = requests.post(url=_url('/messages'),json=payload, headers=headers)
    dict = json.loads(resp.text)
    dict['statuscode']=str(resp.status_code)
    return dict

def get_memberships(at, roomId):
    headers = {'Authorization':at,'content-type':'application/json'}
    payload = {'roomId':roomId}
    resp = requests.get(_url('/memberships'),params=payload, headers=headers)
    dict = json.loads(resp.text)
    dict['statuscode']=str(resp.status_code)
    return dict

def parse_natural_text(user_text):  
    request = ai.text_request()
    request.query = user_text
    logging.debug("The request passed to the API.AI: " + request.query)
    # Receiving the response.
    response = json.loads(request.getresponse().read().decode('utf-8'))
    responseStatus = response['status']['code']
    logging.debug("The response code from API.AI: " + str(response['status']['code']))
    if (responseStatus == 200):
        # Sending the textual response of the bot.
        if not response['result']['fulfillment']['speech']:
            return ("Sorry, I couldn't understand that question")
        else:
            return (response['result']['fulfillment']['speech'])
    else:
        return ("Sorry, I couldn't understand that question")

list_of_emails = []

def get_all_the_users_to_send_questions_to(accesstoken, roomID):
    all_the_members = get_memberships(accesstoken,roomID)['items']
    for i in range(len(all_the_members)):
        list_of_emails.append(all_the_members[i]['personEmail'])
    #print(list_of_emails)
    list_of_emails_to_exclude = ['Botforpipeline@sparkbot.io','eButler@sparkbot.io','dimon@cisco.com','findmysip@sparkbot.io','spark-cisco-it-admin-bot@cisco.com']
    for n in list_of_emails_to_exclude:
        try:
            list_of_emails.remove(n)
        except ValueError:
            pass
    return list_of_emails

def insert_pointer_into_mongodb(data, user_email):
    from pymongo import MongoClient
    #serverSelectionTimeoutMS let us proceed with the bot script even if the DB is not reachable
    client = pymongo.MongoClient(host=['localhost:27017'],serverSelectionTimeoutMS=1000)
    db = client.exampledb
    user_email_pointer = 'Pointer' + user_email
    print(user_email_pointer)
    collection = db[user_email_pointer]
    print(collection)
    #Exception handling, catching everything as there might be some specific errors
    try:
        result=db[user_email_pointer].insert_one(data)
        print(result)
    except Exception as e:
        logging.debug("ERROR: with MongoDB {0}".format(e))    
    client.close()
    return 

def insert_data_into_mongodb(data, user_email):
    from pymongo import MongoClient
    #serverSelectionTimeoutMS let us proceed with the bot script even if the DB is not reachable
    client = pymongo.MongoClient(host=['localhost:27017'],serverSelectionTimeoutMS=1000)
    db = client.exampledb
    user_collection = 'Message_' + user_email
    print(user_collection)
    collection = db[user_collection]
    #Exception handling, catching everything as there might be some specific errors
    try:
        result=db[user_collection].insert_one(data)
        print(result)
    except Exception as e:
        logging.debug("ERROR: with MongoDB {0}".format(e))    
    client.close()
    return True

def get_data_from_mongodb(user_email,limit):
    from pymongo import MongoClient
    #serverSelectionTimeoutMS let us proceed with the bot script even if the DB is not reachable
    client = pymongo.MongoClient(host=['localhost:27017'],serverSelectionTimeoutMS=1000)
    db = client.exampledb
    user_collection = 'Message_' + user_email
    print(user_collection)
    collection = db[user_collection]
    #Exception handling, catching everything as there might be some specific errors
    try:
        result=db[user_collection].find().limit(limit).sort([('$natural', -1)])
        #for doc in result:
            #return doc['pointer']
        print(result)
    except Exception as e:
        logging.debug("ERROR: with MongoDB {0}".format(e))    
    client.close()
    return True

def get_pointer_from_mongodb(user_email):
    from pymongo import MongoClient
    #serverSelectionTimeoutMS let us proceed with the bot script even if the DB is not reachable
    client = pymongo.MongoClient(host=['localhost:27017'],serverSelectionTimeoutMS=1000)
    db = client.exampledb
    user_email_pointer = 'Pointer' + user_email
    collection = db[user_email_pointer]
    #Exception handling, catching everything as there might be some specific errors
    try:
        #result=db[user_email_pointer].find().limit(1).sort({'$natural':-1})
        result=db[user_email_pointer].find().limit(1).sort([('$natural', -1)])
        #result=db[user_email_pointer].find().limit(1)
        for doc in result:
            return doc['pointer']
    except Exception as e:
        logging.debug("ERROR: with MongoDB {0}".format(e))    
    client.close()
    return True

def define_response_based_keywords(message):
    if message == 'help' or message == 'manual':
        return "Help description"
    else:
        pass

def 


message1 = 'Hello User. Please, answer 3 following questions, Please!'

for email_address in get_all_the_users_to_send_questions_to(accesstoken, roomID):
    #post_message_based_on_email(accesstoken,email_address,message1)
    #insert_pointer_into_mongodb ({'pointer':3}, email_address)
    get_pointer_from_mongodb(email_address)

today = datetime.date.today().isoformat()
#today = '2017-09-22'


@app.route("/", methods=['POST'])
def handle_message():
    me = spark_api.people.me()
    data = request.get_json()
    logging.debug("Data received from the WebHook to Flask app:")
    logging.debug(data)
    msgid=data["data"]["id"]
    logging.debug("Retreived message id: " + msgid)
    roomid=data["data"]["roomId"]
    logging.debug("Retereived roomId: " + roomid)
    txt=get_message(accesstoken,msgid)
    logging.debug("Retereived Message: " + txt['text'])
    message=str(txt["text"]).lower()
    possible_response = define_response_based_keywords(message)
    personid=data["data"]["personId"]
    personEmail = data["data"]["personEmail"]
    Pointer = get_pointer_from_mongodb(personEmail)
    if personid==me.id:
        return 'OK'
    elif possible_response:
        resp_dict = post_message(accesstoken,roomid,possible_response)
    elif not Pointer:
        resp_dict = post_message(accesstoken,roomid,parse_natural_text(message))
        return True
    elif Pointer == 0:
        resp_dict = post_message(accesstoken,roomid,parse_natural_text(message))
#to add the abbility to insert messages into the mongodb

    else:
        resp_dict = post_message(accesstoken,roomid,parse_natural_text(message))
    return "OK"