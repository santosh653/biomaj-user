import ssl
import os
import threading
import logging
import random
import string
import yaml
from flask import Flask
from flask import jsonify
from flask import g
from flask import request
from flask import Response
from flask import abort
import consul

from biomaj_user.user import BmajUser

config_file = 'config.yml'
if 'BIOMAJ_CONFIG' in os.environ:
        config_file = os.environ['BIOMAJ_CONFIG']

config = None
with open(config_file, 'r') as ymlfile:
    config = yaml.load(ymlfile)

BmajUser.set_config(config)

app = Flask(__name__)


def start_server(config):
    context = None
    if config['tls']['cert']:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(config['tls']['cert'], config['tls']['key'])

    if config['consul']['host']:
        consul_agent = consul.Consult(host=config['consul']['host'])
        consul_agent.agent.service.register('biomaj_user', service_id=config['consul']['id'], port=config['web']['port'], tags=['biomaj'])
        check = consul.Check.http(url=config['web']['local_endpoint'], interval=20)
        consul_agent.agent.check.register(name + '_check', check=check, service_id=config['consul']['id'])


    app.run(host='0.0.0.0', port=config['web']['port'], ssl_context=context, threaded=True, debug=config['web']['debug'])

@app.route('/api/info/user', methods=['GET'])
def list_users():
    '''
    Check if listing request is over
    '''
    users = BmajUser.list()
    for user in users:
        del user['_id']
        del user['hashed_password']
    return jsonify({'users': users})

@app.route('/api/info/user/<user>', methods=['GET'])
def get_user(user):
    '''
    Check if listing request is over
    '''
    user = BmajUser(user)
    if not user.user:
        abort(404)
    del user.user['_id']
    del user.user['hashed_password']
    return jsonify({'user': user.user})

@app.route('/api/info/user/<user>', methods=['POST'])
def create_user(user):
    '''
    Check if listing request is over
    '''
    user = BmajUser(user)
    param = request.get_json()
    if 'password' not in param:
        param['password'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    if 'email' not in param:
        param['email'] = None
    if not user.user:
        user.create(password=param['password'],email=param['email'])
    del user.user['_id']
    del user.user['hashed_password']        
    return jsonify({'user': user.user, 'password': param['password']})

@app.route('/api/bind/user/<user>', methods=['POST'])
def bind_user(user):
    '''
    Bind a user with his password or API Key. Post parameters dict:

    {'type': 'password|apikey', 'value': 'XXXX'}


    '''
    user = BmajUser(user)
    params = request.get_json()
    check = False
    if params['type'] == 'password':
        check = user.check_password(params['value'])
    else:
        check = user.check_api_key(params['value'])
    if not check:
        abort(401)
    del user.user['_id']
    del user.user['hashed_password']
    return jsonify({'user': user.user})

if __name__ == "__main__":
    start_server(config)
