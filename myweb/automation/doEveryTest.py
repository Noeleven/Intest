#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import configparser

cf = configparser.ConfigParser()
cf.read("/rd/pystudy/conf")
ids = cf.get('automation', 'groupID')
url = 'http://10.113.1.35:7000/auto/auto_config?vals=%s&mytype=group&device=AD' % ids
print(url)
# r = requests.get(url)
