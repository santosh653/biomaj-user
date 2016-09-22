from builtins import str
from builtins import object
import bcrypt
import logging
import random
import string

from pymongo import MongoClient


class BmajUser(object):
    """
    Biomaj User
    """

    config = None

    client = None
    db = None
    banks = None
    users = None

    @staticmethod
    def set_config(config):
        BmajUser.config = config
        BmajUser.client = MongoClient(BmajUser.config['mongo']['url'])
        BmajUser.db = BmajUser.client[BmajUser.config['mongo']['db']]
        BmajUser.banks = BmajUser.db.banks
        BmajUser.users = BmajUser.db.users

    @staticmethod
    def get_user_by_apikey(apikey):
        return BmajUser.users.find_one({'apikey': apikey})

    def __init__(self, user):
        self.id = user
        self.user = BmajUser.users.find_one({'id': user})

        ldap_server = None
        con = None
        if not self.user and BmajUser.config['ldap']['host']:
            # Check if in ldap
            from ldap3 import Server, Connection, STRATEGY_SYNC, SEARCH_SCOPE_WHOLE_SUBTREE, GET_ALL_INFO
            try:
                ldap_host = BmajUser.config['ldap']['host']
                ldap_port = BmajUser.config['ldap']['port']
                ldap_server = Server(ldap_host, port=ldap_port, get_info=GET_ALL_INFO)
                con = Connection(ldap_server, auto_bind=True, client_strategy=STRATEGY_SYNC, check_names=True)
            except Exception as err:
                logging.error(str(err))
                self.user = None
            ldap_dn = BmajUser.config['ldap']['dn']
            base_dn = 'ou=People,' + ldap_dn
            ldapfilter = "(&(|(uid=" + user + ")(mail=" + user + ")))"
            try:
                attrs = ['mail']
                con.search(base_dn, ldapfilter, SEARCH_SCOPE_WHOLE_SUBTREE, attributes=attrs)
                if con.response:
                    ldapMail = None
                    for r in con.response:
                        # user_dn = str(r['dn'])
                        if 'mail' not in r['attributes']:
                            logging.error('Mail not set for user ' + user)
                        else:
                            ldapMail = r['attributes']['mail'][0]
                    self.user = {
                        'id': user,
                        'email': ldapMail,
                        'is_ldap': True,
                        'apikey': ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
                    }
                    self.user['_id'] = self.users.insert(self.user)

                else:
                    self.user = None
            except Exception as err:
                logging.error(str(err))
            if con:
                con.unbind()

    @staticmethod
    def user_remove(user_name):
        """
        Remove a user from db

        :param user_name: user name
        :type user_name: str
        """
        BmajUser.users.remove({'id': user_name})

    @staticmethod
    def list():
        """
        Get users
        """
        users = []
        user_list = BmajUser.users.find()
        for user in user_list:
            users.append(user)
        return users

    def check_apikey(self, apikey):
        if self.user is None:
            return False
        if 'apikey' not in self.user:
            return False
        if self.user['apikey'] == apikey:
            return True
        else:
            return False

    def check_password(self, password):
        if self.user is None:
            return False

        if self.user['is_ldap']:
            con = None
            ldap_server = None

            from ldap3 import Server, Connection, AUTH_SIMPLE, STRATEGY_SYNC, SEARCH_SCOPE_WHOLE_SUBTREE, GET_ALL_INFO
            from ldap3.core.exceptions import LDAPBindError
            try:
                ldap_host = BmajUser.config['ldap']['host']
                ldap_port = BmajUser.config['ldap']['port']
                ldap_server = Server(ldap_host, port=ldap_port, get_info=GET_ALL_INFO)
                con = Connection(ldap_server, auto_bind=True, client_strategy=STRATEGY_SYNC, check_names=True)
            except Exception as err:
                logging.error(str(err))
                return False
            ldap_dn = BmajUser.config['ldap']['dn']
            base_dn = 'ou=People,' + ldap_dn
            ldapfilter = "(&(|(uid=" + self.user['id'] + ")(mail=" + self.user['id'] + ")))"

            try:
                attrs = ['mail']
                con.search(base_dn, ldapfilter, SEARCH_SCOPE_WHOLE_SUBTREE, attributes=attrs)
                user_dn = None
                # ldapMail = None
                # ldapHomeDirectory = None
                for r in con.response:
                    user_dn = str(r['dn'])
                    # ldapMail = r['attributes']['mail'][0]

                con.unbind()
                con = Connection(ldap_server, auto_bind=True, read_only=True, client_strategy=STRATEGY_SYNC, user=user_dn, password=password, authentication=AUTH_SIMPLE, check_names=True)
                con.unbind()

                if user_dn:
                    return True
            except LDAPBindError as err:
                logging.error('Bind error: ' + str(err))
                return False
            except Exception as err:
                logging.error('Bind error: ' + str(err))
                return False

        else:
            hashed = bcrypt.hashpw(password, self.user['hashed_password'])
            if hashed == self.user['hashed_password']:
                return True
            else:
                return False

    def remove(self):
        if self.user is None:
            return False
        BmajUser.users.remove({'_id': self.user['_id']})
        return True

    def create(self, password, email=''):
        """
        Create a new user
        """
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        if self.user is None:
            self.user = {
                'id': self.id,
                'hashed_password': hashed,
                'email': email,
                'is_ldap': False,
                'apikey': ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
            }
            self.user['_id'] = BmajUser.users.insert(self.user)

    def renew_apikey(self):
        api_key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))
        BmajUser.users.update({'_id': self.user['_id']}, {'$set': {'apikey': api_key}})
