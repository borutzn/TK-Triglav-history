#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
program by Borut Žnidar on 12.12.2014
"""

import os


def checkFile( root, fname ):
    new_fname = ""
    for c in fname:
        if ord(c) <= 128:
            new_fname += c
        elif ord(c) == 138:
            new_fname += 'Š'
        elif ord(c) == 142:
            new_fname += 'Ž'
        elif ord(c) == 154:
            new_fname += 'š'
        elif ord(c) == 158:
            new_fname += 'ž'
        else:
            print( ord(c) )

    if fname == new_fname:
        return

    os.rename( os.path.join(root,fname), os.path.join(root,new_fname) )


try:
    for root, dir, files in os.walk( os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/files/') ):
        print( "DIR: " + str(root) )
        for fname in files:
            checkFile( root, fname )
except ValueError: # No files in directory - nothing to select from
    skip        
