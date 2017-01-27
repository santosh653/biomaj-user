import ssl
import os
import random
import string
import yaml
from flask import Flask
from flask import jsonify
from flask import request
from flask import abort
import consul

from biomaj_user.user import BmajUser
from biomaj_core.utils import Utils

config_file = 'config.yml'
if 'BIOMAJ_CONFIG' in os.environ:
        config_file = os.environ['BIOMAJ_CONFIG']

config = None
with open(config_file, 'r') as ymlfile:
    config = yaml.load(ymlfile)
    Utils.service_config_override(config)

BmajUser.set_config(config)

app = Flask(__name__)


def consul_declare(config):
    if config['consul']['host']:
        consul_agent = consul.Consul(host=config['consul']['host'])
        consul_agent.agent.service.register('biomaj-user', service_id=config['consul']['id'], address=config['web']['hostname'], port=config['web']['port'], tags=['biomaj'])
        check = consul.Check.http(url='http://' + config['web']['hostname'] + ':' + str(config['web']['port']) + '/api/user', interval=20)
        consul_agent.agent.check.register(config['consul']['id'] + '_check', check=check, service_id=config['consul']['id'])


consul_declare(config)


@app.route('/api/user', methods=['GET'])
def ping():
    return jsonify({'msg': 'pong'})


@app.route('/api/user/info/user', methods=['GET'])
def list_users():
    '''
    List users
    '''
    users = BmajUser.list()
    for user in users:
        del user['_id']
        del user['hashed_password']
    return jsonify({'users': users})


@app.route('/api/user/info/user/<user>', methods=['GET'])
def get_user(user):
    '''
    Get user info
    '''
    user = BmajUser(user)
    if not user.user:
        abort(404)
    del user.user['_id']
    del user.user['hashed_password']
    return jsonify({'user': user.user})


@app.route('/api/user/info/user/<user>', methods=['POST'])
def create_user(user):
    '''
    Create a user
    '''
    user = BmajUser(user)
    param = request.get_json()
    if 'password' not in param:
        param['password'] = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    if 'email' not in param:
        param['email'] = None
    if not user.user:
        user.create(password=param['password'], email=param['email'])
    del user.user['_id']
    del user.user['hashed_password']
    return jsonify({'user': user.user, 'password': param['password']})


@app.route('/api/user/bind/user/<user>', methods=['POST'])
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
        check = user.check_apikey(params['value'])
    if not check:
        abort(401)
    del user.user['_id']
    del user.user['hashed_password']
    return jsonify({'user': user.user})


@app.route('/api/user/info/apikey/<apikey>', methods=['GET'])
def get_user_by_apikey(apikey):
    '''
    Get a user from his api key
    '''
    user = BmajUser.get_user_by_apikey(apikey)
    if user:
        del user['_id']
        if 'hashed_password' in user:
            del user['hashed_password']
    return jsonify({'user': user})


if __name__ == "__main__":
    context = None
    if config['tls']['cert']:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain(config['tls']['cert'], config['tls']['key'])
    app.run(host='0.0.0.0', port=config['web']['port'], ssl_context=context, threaded=True, debug=config['web']['debug'])
