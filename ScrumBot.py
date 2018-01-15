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

accesstoken="ZGVjNzhkYjQtMTkzZi00YTc5LTk0ZjAtZmE5OTJkNmIyN2Y3Mjg1ZGE1OGQtZjkx"
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

def post_message_with_markdown(at,roomId,text,markdown):
    headers = {'Authorization':at, 'content-type':'application/json'}
    payload = {'roomId':roomId, 'text':text, 'markdown':markdown}
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
    domains_to_exclude = '@sparkbot.io'
    all_the_members = get_memberships(accesstoken,roomID)['items']
    for i in range(len(all_the_members)):
        list_of_emails.append(all_the_members[i]['personEmail'])
    #print(list_of_emails)
    list_of_emails_to_exclude = ['eButler@sparkbot.io','dimon@cisco.com','findmysip@sparkbot.io','spark-cisco-it-admin-bot@cisco.com']
    for i in list_of_emails:
        if domains_to_exclude in i:
            list_of_emails_to_exclude.append(i)
            #print(list_of_emails_to_exclude)
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

def insert_data_into_mongodb(data, user_email, pointer):
    from pymongo import MongoClient
    #serverSelectionTimeoutMS let us proceed with the bot script even if the DB is not reachable
    client = pymongo.MongoClient(host=['localhost:27017'],serverSelectionTimeoutMS=1000)
    db = client.exampledb
    user_collection = 'Message_' + user_email
    print(user_collection)
    collection = db[user_collection]
    #Exception handling, catching everything as there might be some specific errors
    try:
        data['Pointer'] = pointer
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
   # print(user_collection)
    collection = db[user_collection]
    list_of_answers = []
    #Exception handling, catching everything as there might be some specific errors
    try:
        result=db[user_collection].find().limit(limit).sort([('$natural', -1)])
        #print(result)
        for doc in result:
            list_of_answers.append(doc['text'])
        #print (list_of_answers)
        return list_of_answers
            #return doc['text']            
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
        return False    
    client.close()
    #return True


help_message = 'Hello. My name is ScrumBotIBM. I\'m helpin the project team with daily tasks. Please, contact dmkravch@cisco.com if you need more inforamtion about the bot, or ahermoso@cisco.com if you need more inforamtion about the project. Thank you.'
def define_response_based_keywords(message):
    if 'help' in message or 'manual' in message:
        return help_message
    else:
        pass

today = datetime.date.today().isoformat()

message0 = 'Hello!  Today is ' + today + '!   Please, answer 3 following questions about the project!'
message1 = '1.  What did you do yesterday?'
message2 = '2.  What will you do today?'
message3 = '3.  Are there any impediments in your way?'
message4 = 'Thank you! Your answers will be posted in the General space.'
message5 = 'Team. Today\'s report from '




#text = 'Hi ' + user_email +' your order has been processed.'
#markdown = 'Hi <@personEmail:' + user_email + '|Dmytro>, your order has been processed.'
#a = get_all_the_users_to_send_questions_to(accesstoken, roomID)
#print(a)
now = datetime.datetime.now()
if 9 <= now.hour <= 10:
    for email_address in get_all_the_users_to_send_questions_to(accesstoken, roomID):
        post_message_based_on_email(accesstoken,email_address,message0)
        post_message_based_on_email(accesstoken,email_address,message1)
        #post_message_with_markdown(accesstoken, roomId, text, markdown)
        insert_pointer_into_mongodb ({'pointer':1}, email_address)

    #get_pointer_from_mongodb(email_address)

a = '**'
webhook_id = 'Y2lzY29zcGFyazovL3VzL1dFQkhPT0svOTJhYWE1NzctNTU0ZC00YTZlLTljM2MtNDAzNWU1N2RkYTQy'

@app.route("/", methods=['POST'])
def handle_message():
    me = spark_api.people.me()
    data = request.get_json()
    if data["id"] != webhook_id:
        logging.debug("Retereived Webhook_id doesnt match. Retreived: " + data["id"])
        msgid=data["data"]["id"]
        txt=get_message(accesstoken,msgid)
        user_email = data["data"]["personEmail"]
        insert_data_into_mongodb(txt, user_email, 666)
        return 'ok' 
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
    user_email = data["data"]["personEmail"]
    Pointer = get_pointer_from_mongodb(user_email)
    logging.debug("Retreived pointer: "+str(Pointer))
    if personid==me.id:
        return 'OK'
    elif not Pointer:
        logging.debug("If not Pointer: "+str(Pointer))
        insert_data_into_mongodb(txt, user_email, 999)
        resp_dict = post_message(accesstoken,roomid,help_message)
        insert_pointer_into_mongodb ({'pointer':20}, user_email)
    elif Pointer == 10:
        if possible_response:
            logging.debug("possible_response: "+ possible_response)
            resp_dict = post_message(accesstoken,roomid,possible_response)
            insert_data_into_mongodb(txt, user_email, Pointer)
        else:           
            logging.debug("Pointer 0: "+str(Pointer))
            resp_dict = post_message(accesstoken,roomid,parse_natural_text(message))
            insert_data_into_mongodb(txt, user_email, Pointer)
    elif Pointer == 1:
        logging.debug("Pointer 1: "+str(Pointer))
        resp_dict = post_message(accesstoken,roomid,message2)
        insert_data_into_mongodb(txt, user_email, Pointer)
        insert_pointer_into_mongodb ({'pointer':2}, user_email)
    elif Pointer == 2:
        logging.debug("Pointer 2: "+str(Pointer))
        resp_dict = post_message(accesstoken,roomid,message3)
        insert_data_into_mongodb(txt, user_email, Pointer)
        insert_pointer_into_mongodb ({'pointer':3}, user_email)
    elif Pointer == 3:
        logging.debug("Pointer 3: "+str(Pointer))
        resp_dict = post_message(accesstoken,roomid,message4)
        insert_data_into_mongodb(txt, user_email,Pointer)
        insert_pointer_into_mongodb ({'pointer':10}, user_email)
        list_of_answers = get_data_from_mongodb(user_email,3)
        post_to_general_space = message5 + user_email + '\n'+  message1 +'\n'+  list_of_answers[2] + '\n'
        post_to_general_space_with_markdown = message5 + '<@personEmail:' + user_email + '>' +'  \n  '+ message1 +'  \n  '+ a + list_of_answers[2] + a + '  \n  ' + message2 + '  \n  ' + a + list_of_answers[1] +a + '  \n  ' + message3 + '  \n  ' + a + list_of_answers[0] + a
        post_to_general_space = post_to_general_space + message2 + '\n' + list_of_answers[1] + '\n'
        post_to_general_space = post_to_general_space + message3 + '\n' + list_of_answers[0]
        roomid = 'Y2lzY29zcGFyazovL3VzL1JPT00vODZjYzg4NzAtNjdjYy0xMWU3LTgxZTYtYzM1MDA1YTVkZTFj'
        #resp_dict = post_message(accesstoken,roomid,post_to_general_space)
        resp_dict = post_message_with_markdown(accesstoken, roomid, post_to_general_space, post_to_general_space_with_markdown)
    elif possible_response:
        logging.debug("possible_response: "+ possible_response)
        resp_dict = post_message(accesstoken,roomid,possible_response)
        insert_data_into_mongodb(txt, user_email, Pointer)
    else:
        logging.debug("Entering the last else statement. ")
        resp_dict = post_message(accesstoken,roomid,parse_natural_text(message))
    return "OK"