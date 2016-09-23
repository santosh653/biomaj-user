import ssl
import os
import random
import string
import yaml
import sys

from biomaj_user.user import BmajUser

config_file = 'config.yml'
if 'BIOMAJ_CONFIG' in os.environ:
        config_file = os.environ['BIOMAJ_CONFIG']

config = None
with open(config_file, 'r') as ymlfile:
    config = yaml.load(ymlfile)

BmajUser.set_config(config)

if len(sys.argv) == 1:
    print("USer id is missing in arguments")

user = BmajUser(sys.argv[1])
if user.user is None:
    password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
    user.create(password)
    print("User created with password: " + password)

print(str(user.user))
