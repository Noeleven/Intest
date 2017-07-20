#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import configparser

cf = configparser.ConfigParser()
cf.read("/rd/pystudy/conf")
mids = cf.get('automation', 'MgroupID').split(',')
for x in mids:
	url = 'http://127.0.0.1:8000/auto/auto_config?vals=%s&type=group&device=M&isDay=yes' % x
	print(url)
	r = requests.get(url)
