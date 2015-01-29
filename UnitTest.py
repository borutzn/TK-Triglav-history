#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Borut'

# import os
import mainTennis
import unittest
# import tempfile


class MainTennisTestCase(unittest.TestCase):

    def setUp(self):
        self.app = mainTennis.app.test_client()

    def tearDown(self):
        pass

    def login(self, username, password):
        return self.app.post('/login', data=dict(username=username, password=password), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('borut1', 'borut')
        assert u'Prijava uspeš' in rv.data
        rv = self.logout()
        assert u'Odjava uspe' in rv.data
        rv = self.login('adminx', 'default')
        assert u'Prijava neuspe' in rv.data
        # rv = self.login('admin', 'defaultx')
        # print( str(rv.data)[:1000] )
        # assert 'Prijava neuspe' in rv.data

if __name__ == '__main__':
    unittest.main()