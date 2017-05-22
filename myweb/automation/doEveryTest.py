#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import configparser

cf = configparser.ConfigParser()
cf.read("/rd/pystudy/conf")
ids = cf.get('automation', 'groupID')
for x in ids:
	url = 'http://10.113.1.35:8000/auto/auto_config?vals=%s&type=group&device=AD&isDay=yes' % x
	print(url)
	r = requests.get(url)
