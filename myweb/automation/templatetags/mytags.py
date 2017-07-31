#!/usr/lib/env python3
#! -*- coding:utf-8 -*-

from django import template

register = template.Library()

# def trans_time(ms):
#     if 'ms' in ms:
#         s = ms / 1000
#         m,n = divmod(s, 60)
#         result = '' % (m,n)
#         return
#     else:
#         return s
