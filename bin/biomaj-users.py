import argparse
from argparse import Namespace as options
import os
import random
import yaml
import string
import sys
import bcrypt
from tabulate import tabulate
from biomaj_user.user import BmajUser
from biomaj_core.utils import Utils
SUPPORTED_ACTIONS = ['add', 'create', 'delete', 'remove', 'rm', 'renew', 'update', 'view']


def main():
    """This is the main function treating arguments passed on the command line."""
    description = "BioMAJ user: Manager users."
    parser = argparse.ArgumentParser(description=description)
    # Options without value
    parser.add_argument('-A', '--action', dest="action", default=None,
                        help="Action to perform for user " + str(SUPPORTED_ACTIONS) +
                             "'renew': Create new api key",
                        required=True)
    parser.add_argument('-C', '--config', dest="config", metavar='</path/to/config.yml>', type=str,
                        help="Path to config.yml. By default read from env variable BIOMAJ_CONFIG")
    parser.add_argument('-E', '--email', dest="email", type=str,
                        help="User email, optional")
    parser.add_argument('-U', '--user', dest="user", metavar='<username>', type=str,
                        required=True, help="User name to manage")
    parser.add_argument('-P', '--password', dest="passwd", metavar="<password>", type=str,
                        help="User password to use when creating new user. If not given, automatically generated, accepts env variable BIOMAJ_USER_PASSWORD env variable")
    parser.parse_args(namespace=options)
    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit(1)
    if options.action not in SUPPORTED_ACTIONS:
        print("Unsupported action '%s'" % str(options.action))
        sys.exit(1)

    if options.config:
        config = options.config
    elif 'BIOMAJ_CONFIG' in os.environ:
        config = os.environ['BIOMAJ_CONFIG']
    else:
        config = 'config.yml'
    with open(config, 'r') as ymlfile:
        config = yaml.load(ymlfile)
        Utils.service_config_override(config)

    BmajUser.set_config(config)
    user = BmajUser(options.user)
    if options.action in ['add', 'create']:
        if user.user is None:
            if options.passwd is None:
                if 'BIOMAJ_USER_PASSWORD' in os.environ:
                    options.passwd = os.environ['BIOMAJ_USER_PASSWORD']
                else:
                    options.passwd = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits)
                                         for _ in range(10))
            user.create(options.passwd, email=options.email)
            print("User successfully created")
            print(tabulate([["User", "Password", "API Key"],
                            [user.user['id'], str(options.passwd), str(user.user['apikey'])]],
                           headers="firstrow", tablefmt="psql"))
            sys.exit(0)
        else:
            print("User %s already exist" % user.user['id'])
            sys.exit(1)

    if user.user is None:
        print("[%s] User %s does not exist" % (str(options.action), str(options.user)))
        sys.exit(1)

    if options.action in ['delete', 'remove', 'rm']:
        user.remove()
        print("User %s successfully deleted" % user.user['id'])
    if options.action == 'update':
        update = {}
        if options.passwd:
            update['hashed_password'] = bcrypt.hashpw(options.passwd, user.user['hashed_password'])
        if options.email:
            update['email'] = options.email
        if update.items():
            BmajUser.users.update({'id': user.user['id']}, {'$set': update})
            print("User %s successfully updated" % str(user.user['id']))
        else:
            print("[%s] User %s not updated" % (str(options.action), str(options.user)))
    if options.action == 'renew':
        user.renew_apikey()
        user = BmajUser(user.user['id'])
        print("[%s] User %s, successfully renewed API key: '%s'" %
              (str(options.action), str(user.user['id']), str(user.user['apikey'])))
    if options.action == 'view':
        print(tabulate([["User", "Email", "API Key", "LDAP"],
                        [str(user.user['id']), str(user.user['email']),
                         str(user.user['apikey']), str(user.user['is_ldap'])]],
                       headers="firstrow", tablefmt="psql"))
    sys.exit(0)

if __name__ == '__main__':
    main()
