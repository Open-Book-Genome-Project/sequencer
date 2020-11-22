#!/usr/bin/env python3

"""
    :copyright: (c) 2020 by Open Book Genome Project
    :license: BSD, see LICENSE for more details.
"""

import configparser
import os
import sys
import types

path = os.path.dirname(os.path.realpath(__file__))
approot = os.path.abspath(os.path.join(path, os.pardir))

def getdef(self, section, option, default_value):
    try:
        return self.get(section, option)
    except:
        return default_value

config = configparser.ConfigParser()
config.read('%s/settings.cfg' % path)
config.getdef = types.MethodType(getdef, config)

S3_KEYS = {
    'access': config.getdef('s3', 'access', ''),
    'secret': config.getdef('s3', 'secret', '')
}


