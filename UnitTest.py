#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'Borut'

# import os
import mainTennis
import unittest
# import tempfile


class MainTennisTestCase(unittest.TestCase):

    def setUp(self):
        # self.db_fd, mainTennis.app.config['DATABASE'] = tempfile.mkstemp()
        # mainTennis.app.config['TESTING'] = True
        self.app = mainTennis.app.test_client()

    def tearDown(self):
        # os.close(self.db_fd)
        # os.unlink(mainTennis.app.config['DATABASE'])
        pass

    def login(self, username, password):
        return self.app.post('/login', data=dict(username=username, password=password), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_logout(self):
        rv = self.login('borut1', 'borut')
        print( str(rv) )
        assert 'Prijava uspešna' in rv.data
        rv = self.logout()
        assert 'Odjava uspešna' in rv.data
        rv = self.login('adminx', 'default')
        assert 'Invalid username' in rv.data
        rv = self.login('admin', 'defaultx')
        assert 'Invalid password' in rv.data

if __name__ == '__main__':
    unittest.main()