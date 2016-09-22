from nose.tools import *
from nose.plugins.attrib import attr

import json
import shutil
import os
import tempfile
import logging
import copy
import stat
import time

from mock import patch

from optparse import OptionParser

from biomaj_core.config import BiomajConfig
from biomaj_core.utils import Utils

from biomaj_user.user import BmajUser

import unittest

class UtilsForTest():
  """
  Copy properties files to a temp directory and update properties to
  use a temp directory
  """

  def __init__(self):
    """
    Setup the temp dirs and files.
    """
    self.global_properties = None
    self.bank_properties = None

    self.test_dir = tempfile.mkdtemp('biomaj')

    self.conf_dir =os.path.join(self.test_dir,'conf')
    if not os.path.exists(self.conf_dir):
      os.makedirs(self.conf_dir)
    self.data_dir =os.path.join(self.test_dir,'data')
    if not os.path.exists(self.data_dir):
      os.makedirs(self.data_dir)
    self.log_dir =os.path.join(self.test_dir,'log')
    if not os.path.exists(self.log_dir):
      os.makedirs(self.log_dir)
    self.process_dir =os.path.join(self.test_dir,'process')
    if not os.path.exists(self.process_dir):
      os.makedirs(self.process_dir)
    self.lock_dir =os.path.join(self.test_dir,'lock')
    if not os.path.exists(self.lock_dir):
      os.makedirs(self.lock_dir)
    self.cache_dir =os.path.join(self.test_dir,'cache')
    if not os.path.exists(self.cache_dir):
      os.makedirs(self.cache_dir)


    if self.global_properties is None:
      self.__copy_global_properties()


  def clean(self):
    """
    Deletes temp directory
    """
    shutil.rmtree(self.test_dir)


  def __copy_global_properties(self):
    if self.global_properties is not None:
      return
    self.global_properties = os.path.join(self.conf_dir,'global.properties')
    curdir = os.path.dirname(os.path.realpath(__file__))
    global_template = os.path.join(curdir,'global.properties')
    fout = open(self.global_properties,'w')
    with open(global_template,'r') as fin:
        for line in fin:
          if line.startswith('conf.dir'):
            fout.write("conf.dir="+self.conf_dir+"\n")
          elif line.startswith('log.dir'):
            fout.write("log.dir="+self.log_dir+"\n")
          elif line.startswith('data.dir'):
            fout.write("data.dir="+self.data_dir+"\n")
          elif line.startswith('process.dir'):
            fout.write("process.dir="+self.process_dir+"\n")
          elif line.startswith('lock.dir'):
            fout.write("lock.dir="+self.lock_dir+"\n")
          else:
            fout.write(line)
    fout.close()


class MockLdapConn(object):

  ldap_user = 'biomajldap'
  ldap_user_email = 'bldap@no-reply.org'

  STRATEGY_SYNC = 0
  AUTH_SIMPLE = 0
  STRATEGY_SYNC = 0
  STRATEGY_ASYNC_THREADED = 0
  SEARCH_SCOPE_WHOLE_SUBTREE = 0
  GET_ALL_INFO = 0

  @staticmethod
  def Server(ldap_host, port, get_info):
      return None

  @staticmethod
  def Connection(ldap_server, auto_bind=True, read_only=True, client_strategy=0, user=None, password=None, authentication=0,check_names=True):
      if user is not None and password is not None:
          if password == 'notest':
              #raise ldap3.core.exceptions.LDAPBindError('no bind')
              return None
      return MockLdapConn(ldap_server)

  def __init__(self, url=None):
    #self.ldap_user = 'biomajldap'
    #self.ldap_user_email = 'bldap@no-reply.org'
    pass

  def search(self, base_dn, filter, scope, attributes=[]):
    if MockLdapConn.ldap_user in filter:
      self.response = [{'dn': MockLdapConn.ldap_user, 'attributes': {'mail': [MockLdapConn.ldap_user_email]}}]
      return [(MockLdapConn.ldap_user, {'mail': [MockLdapConn.ldap_user_email]})]
    else:
      raise Exception('no match')

  def unbind(self):
    pass


@attr('user')
class TestUser(unittest.TestCase):
  """
  Test user management
  """

  def setUp(self):
    self.utils = UtilsForTest()
    self.curdir = os.path.dirname(os.path.realpath(__file__))
    BiomajConfig.load_config(self.utils.global_properties, allow_user_config=False)
    config = {
        'mongo': {
            'url': BiomajConfig.global_config.get('GENERAL', 'db.url'),
            'db': BiomajConfig.global_config.get('GENERAL', 'db.name')
            },
        'ldap': {
            'host': BiomajConfig.global_config.get('GENERAL', 'ldap.host'),
            'port': int(BiomajConfig.global_config.get('GENERAL', 'ldap.port')),
            'dn': BiomajConfig.global_config.get('GENERAL', 'ldap.dn')
            }
    }
    BmajUser.set_config(config)

  def tearDown(self):
    self.utils.clean()

  @patch('ldap3.Connection')
  def test_get_user(self, initialize_mock):
    mockldap = MockLdapConn()
    initialize_mock.return_value = MockLdapConn.Connection(None, None, None, None)
    user = BmajUser('biomaj')
    self.assertTrue(user.user is None)
    user.remove()

  @patch('ldap3.Connection')
  def test_create_user(self, initialize_mock):
    mockldap = MockLdapConn()
    initialize_mock.return_value = MockLdapConn.Connection(None, None, None, None)
    user = BmajUser('biomaj')
    user.create('test', 'test@no-reply.org')
    self.assertTrue(user.user['email'] == 'test@no-reply.org')
    user.remove()

  @patch('ldap3.Connection')
  def test_check_password(self, initialize_mock):
    mockldap = MockLdapConn()
    initialize_mock.return_value = MockLdapConn.Connection(None, None, None, None)
    user = BmajUser('biomaj')
    user.create('test', 'test@no-reply.org')
    self.assertTrue(user.check_password('test'))
    user.remove()

  @patch('ldap3.Connection')
  def test_ldap_user(self, initialize_mock):
    mockldap = MockLdapConn()
    initialize_mock.return_value = MockLdapConn.Connection(None, None, None, None)
    user = BmajUser('biomajldap')
    self.assertTrue(user.user['is_ldap'] == True)
    self.assertTrue(user.user['_id'] is not None)
    self.assertTrue(user.check_password('test'))
    user.remove()

  @patch('ldap3.Connection')
  def test_api_renew(self, initialize_mock):
    mockldap = MockLdapConn()
    initialize_mock.return_value = MockLdapConn.Connection(None, None, None, None)
    user = BmajUser('biomajldap')
    apikey = user.user['apikey']
    user = BmajUser('biomajldap')
    self.assertTrue(user.user['apikey'] == apikey)
    user.renew_apikey()
    user = BmajUser('biomajldap')
    self.assertTrue(user.user['apikey'] != apikey)    
    user.remove()
