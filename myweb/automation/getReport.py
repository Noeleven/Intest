#!/usr/bin/env python
# -*- coding:utf-8 -*-

import requests
import datetime


timeTag = datetime.datetime.now().strftime("%Y%m%d")
url = 'http://10.113.1.35:8000/auto/api_report?timeStamp=autoTestIn%s' % timeTag

r = requests.get(url)

