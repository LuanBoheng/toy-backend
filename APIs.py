from flask import Flask, request, Response
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from flask_jsonpify import jsonify
import json
import pymongo  # pip install pymongo
from bson import json_util 
from pymongo import MongoClient# Comes with pymongo
import random
from bson.objectid import ObjectId
from auto_email import send_email


print('package loaded!')

def get_db():
    try:
        client = MongoClient('mongodb://admin:Gh1QyOay3xC1@localhost:27017')
        db = client['admin']
        return db
    except:
        print('Error: unable to connect mongodb!')
        return None

def POST(collection, post):
    collection = get_db()[collection]
    collection.insert_one(post)

def UPDATE(collection, _id, post): 
    collection = get_db()[collection]
    query = {'_id':ObjectId(_id)}
    new_value = {'$set':post}
    collection.update_one(query, new_value)

def GET(collection, query = None): 
    collection = get_db()[collection]
    results = list(collection.find(query))
    for e in results:
        e['_id'] = str(e['_id'])
   
    results = dict(zip(range(len(results)),results)) 
    results['length'] = len(results)
    return results

class Session_token:
    def __init__(self):
        self.user2token = dict()
        self.token2user = dict()
    
    def new_session(self, email):
        #token = str(os.urandom(32))
        token = str(random.random())[2:]
        self.user2token[email] = token
        self.token2user[token] = email
        return token

    def is_session(self, token):
        return token in self.token2user

token_cache = Session_token()
super_user = ['1', 'susanto.collector@gmail.com', 'susanto.shipper@google.com']

class Test(Resource):
    def get(self, arg):
        return json.dumps({'message':'connection established!', 'arg':arg})

class Login(Resource):
    def get(self, email, password): # for login function
        print('#debug print:', (email, password))
        query =  {'email':email, 'password':password}
        user = GET('user_profile', query)
        if user['length'] == 0:
            message = {'message':'incorrect email or password', 'token':'null'}
        else:
            token = str(token_cache.new_session(email))
            message = {'message':'login successful!', 'token':token}
            print('#debug print',token)
        resp = Response(json.dumps(message))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp 

class Sign_up(Resource):
    def get(self, user_name, password, email, addr, phone_num):
        print('#debug print:', (user_name, password))
        
        user = {
                'user':user_name, 
                'password':password, 
                'email':email,
                'address':addr,
                'phone':phone_num
                }

        user_exist = GET('user_profile',user)['length'] != 0
        print('#debug print: user exist', GET('user_profile',user), user_exist) 
        
        if user_exist:
            message = json.dumps({'message':'user already exist!'})
        else:
            POST('user_profile',user)
            message = json.dumps({'message':'sign up successful!'})
        resp = Response(message)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


class Update_user(Resource):
    def get(self, token, user_name, password, email, addr, phone_num):
        print('#debug print:', (user_name, password))
        target_user_email = token_cache.token2user[token]
        query = {'email':target_user_email}
        print('#debug print', GET('user_profile',query) )
        user_id = GET('user_profile',query)[0]['_id']


        user = {
                'user':user_name, 
                'password':password, 
                'email':email,
                'address':addr,
                'phone':phone_num
                }

        UPDATE('user_profile', user_id, user) 
        message = json.dumps({'message':'user profile updated successful!'})
        resp = Response(message)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


class Update_ack(Resource):
    def get(self, token, order_id, status, time_pickup, message_shipper):
        target_user_email = token_cache.token2user[token]
        if target_user_email in super_user:
            change = {
                    'ack.status':status,
                    'ack.time_pickup':time_pickup,
                    'ack.message_shipper':message_shipper
                     }
            UPDATE('orders', order_id, change)
            message = {'message':'order ACK updated successful!'}
        else:
            message = {'message':'not super user!'}
        message = json.dumps(message)
        resp = Response(message)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        send_email(target_user_email, 'your order ack has been changed')
        return resp


class Shippment(Resource):
    def get(self):
        message = { '0':{
                        'ship_id':'1',
                        'depart_date':'xxxx.xx.x1',
                        'estimate_arrive_date':'xxxx.xx.x1'
                        },
                    '1':{
                        'ship_id':'2',
                        'depart_date':'xxxx.xx.x2',
                        'estimate_arrive_date':'xxxx.xx.x2'
                        },
                    'length':'2'
                    }
        message = json.dumps(message)
        resp = Response(message)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


class Create_order(Resource):
    def get(self, token, num_box, addr_Jakarta, addr_melb, shipment_id, message):
        print('#debug print: token', token)
        email = token_cache.token2user[token]
        
        request = {
                'sender':email,
                'num_box':num_box,
                'addr_dest':addr_Jakarta,
                'addr_pick':addr_melb,
                'shipment_id':shipment_id,
                'message_user':message
                }

        ack = {
                'status':'To be Approved',
                'time_pickup':'',
                'cost':num_box,
                'num_hbl':str(random.random()),
                'message_shipper':''
                }

        order = dict()
        order['request'] = request
        order['ack'] = ack

        POST('orders', order)
        message = json.dumps({'message':'order created successful!'})
        resp = Response(message)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        send_email(email, 'new order has been created')
        return resp


class View_user(Resource):
    def get(self, token):
        email = token_cache.token2user[token]
        user = GET('user_profile',{'email':email})
        user['is_super'] = email in super_user
        message = json.dumps(user)
        resp = Response(message)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


class View_order(Resource):
    def get(self, token):
        print('#debug print: token', token)
        email = token_cache.token2user[token]
        orders = GET('orders', {'request.sender':email})
        if email in super_user:
            orders = GET('orders', {})
            
        message = json.dumps(orders)
        resp = Response(message)
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp




app = Flask(__name__)
api = Api(app)

api.add_resource(Test,'/test/<arg>')
api.add_resource(Shippment,'/ship')
api.add_resource(Login,'/login/<email>/<password>')
api.add_resource(Sign_up,'/signup/<user_name>/<password>/<email>/<addr>/<phone_num>')
api.add_resource(Update_user,'/updateuser/<token>/<user_name>/<password>/<email>/<addr>/<phone_num>')
api.add_resource(Create_order, '/createorder/<token>/<num_box>/<addr_Jakarta>/<addr_melb>/<shipment_id>/<message>')
api.add_resource(View_order,'/vieworder/<token>')
api.add_resource(View_user,'/viewuser/<token>')
api.add_resource(Update_ack,'/updateack/<token>/<order_id>/<status>/<time_pickup>/<message_shipper>')

if __name__ == "__main__":
    #app.run('115.146.92.114', port=8888, ssl_context='adhoc')
    app.run('115.146.92.114', port=8888)

