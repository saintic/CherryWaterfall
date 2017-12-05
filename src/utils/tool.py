# -*- coding: utf-8 -*-
"""
    CherryWaterfall.utils.tool
    ~~~~~~~~~~~~~~

    Common function.

    :copyright: (c) 2017 by Mr.tao.
    :license: MIT, see LICENSE for more details.
"""

import requests, hashlib, datetime, random, upyun, time
from log import Logger
from config import SSO, Upyun
from functools import wraps
from flask import g, request, redirect, url_for

md5 = lambda pwd:hashlib.md5(pwd).hexdigest()
logger = Logger("sys").getLogger
#列表按长度切割
ListEqualSplit = lambda l,n=5: [ l[i:i+n] for i in range(0,len(l), n) ]
#无重复随机数
gen_rnd_filename = lambda :"%s%s" %(datetime.datetime.now().strftime('%Y%m%d%H%M%S'), str(random.randrange(1000, 10000)))
#文件名合法性验证
allowed_file = lambda filename: '.' in filename and filename.rsplit('.', 1)[1] in set(['png', 'jpg', 'jpeg', 'gif'])

def isLogged_in(cookie_str):
    ''' check username is logged in '''

    SSOURL = SSO.get("SSO.URL")
    if cookie_str and not cookie_str == '..':
        username, expires, sessionId = cookie_str.split('.')
        try:
            success = requests.post(SSOURL+"/sso/", data={"username": username, "time": expires, "sessionId": sessionId}, timeout=3, verify=False, headers={"User-Agent": "SSO.Client"}).json().get("success", False)
        except Exception,e:
            logger.error(e, exc_info=True)
        else:
            logger.info("check login request, cookie_str: %s, success:%s" %(cookie_str, success))
            return success
    else:
        logger.info("Not Logged in")
    return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.signin:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def UploadImage2Upyun(FilePath, FileData):
    """ Upload image to Upyun Cloud with Api """
    up = upyun.UpYun(Upyun["bucket"], username=Upyun["username"], password=Upyun["password"], timeout=10, endpoint=upyun.ED_AUTO)
    res = up.put(FilePath, FileData)
    return res

def get_current_timestamp():
    """ 获取本地当前时间戳(10位): Unix timestamp：是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒 """
    return int(time.mktime(datetime.datetime.now().timetuple()))