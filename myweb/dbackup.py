#!/usr/bin/env python3
# -*- coding:utf8 -*-
# 删除仿真测试产生的数据，导出听云数据
from datetime import datetime, timedelta
import configparser
import mysql.connector
import os

now = datetime.now()
real_date = (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')

cf = configparser.ConfigParser()
cf.read('/rd/pystudy/conf')
user = cf.get('db', 'user')
passwd = cf.get('db', 'password')

fz_conn = mysql.connector.connect(user=user, password=passwd, database='intest')
cursor = fz_conn.cursor()
try:
	cursor.execute("delete from fz_sdata where timestamp < '%s'" % real_date)
	fz_conn.commit()
except mysql.connector.Error as e:
	print('===error===:%s' % e)
finally:
	cursor.close()
	fz_conn.close()

os.system('mysqldump -u%s -p%s %s > /rd/pystudy/Intest/myweb/intest/db/tingyun.sql' % (user, passwd, 'tingyun'))
os.system('mysqldump -u%s -p%s %s > /rd/pystudy/Intest/myweb/intest/db/intest.sql' % (user, passwd, 'intest'))
