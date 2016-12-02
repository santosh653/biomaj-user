import ssl
import os
import random
import string
import yaml
import sys

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

if len(sys.argv) == 1:
    print("USer id is missing in arguments")

user = BmajUser(sys.argv[1])
if user.user is not None:
    user.remove()
    print("User removed")
else:
    print("User not found")
