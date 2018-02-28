# -*- coding: utf-8 -*-
"""
    CherryWaterfall.utils.tool
    ~~~~~~~~~~~~~~

    Common function.

    :copyright: (c) 2017 by Mr.tao.
    :license: MIT, see LICENSE for more details.
"""

import requests, hashlib, datetime, random, upyun, time, re
from log import Logger
from config import SSO, Upyun
from functools import wraps
from flask import g, request, redirect, url_for

md5 = lambda pwd:hashlib.md5(pwd).hexdigest()
logger = Logger("sys").getLogger
access_logger = Logger("access").getLogger
comma_pat = re.compile(r"\s*,\s*")
#列表按长度切割
ListEqualSplit = lambda l,n=5: [ l[i:i+n] for i in range(0,len(l), n) ]
#无重复随机数
gen_rnd_filename = lambda :"%s%s" %(datetime.datetime.now().strftime('%Y%m%d%H%M%S'), str(random.randrange(1000, 10000)))
#文件名合法性验证
allowed_file = lambda filename: '.' in filename and filename.rsplit('.', 1)[1] in set(['png', 'jpg', 'jpeg', 'gif', 'mp4'])

def get_current_timestamp():
    """ 获取本地当前时间戳(10位): Unix timestamp：是从1970年1月1日（UTC/GMT的午夜）开始所经过的秒数，不考虑闰秒 """
    return int(time.mktime(datetime.datetime.now().timetuple()))

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

def timestamp_datetime(timestamp, format='%Y-%m-%d %H:%M:%S'):
    """ 将时间戳(10位)转换为可读性的时间 """
    # timestamp为传入的值为时间戳(10位整数)，如：1332888820
    timestamp = time.localtime(timestamp)
    # 经过localtime转换后变成
    ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
    # 最后再经过strftime函数转换为正常日期格式。
    return time.strftime(format, timestamp)

def getSystem(rc, key):
    """查询系统配置"""
    res = {"msg": None, "data": dict()}
    try:
        data = rc.hgetall(key)
    except Exception, e:
        logger.error(e, exc_info=True)
        res.update(msg="query system configure error")
    else:
        """
        site_TitleSuffix: 站点标题后缀
        site_RssTitle: 站点订阅源标题
        site_License: 站点许可证
        site_Copyright: 站点版权
        author_Email: 作者邮箱
        github: 项目github地址
        sys_Close: 是否关闭系统 1:关闭 0:开启 关闭后则首页返回400错误码
        """
        if not data.get("site_TitleSuffix"):
            data.update(site_TitleSuffix=u"樱瀑")
        if not data.get("site_RssTitle"):
            data.update(site_RssTitle=u"樱瀑")
        if not data.get("site_License"):
            data.update(site_License="MIT")
        if not data.get("site_Copyright"):
            data.update(site_Copyright="Copyright © {year}".format(year=datetime.datetime.now().year))
        if not data.get("author_Email"):
            data.update(author_Email="")
        if not data.get("github"):
            data.update(github="https://github.com/staugur/CherryWaterfall")
        if not data.get("sys_Close"):
            data.update(sys_Close=0)
        if not data.get("sso_AllowedUsers"):
            data.update(sso_AllowedUsers="taochengwei")
        if not data.get("site_UploadMax"):
            data.update(site_UploadMax=0)
        if not data.get("site_UploadSize"):
            data.update(site_UploadSize=2048)
        res.update(data=data)
    return res

def setSystem(rc, key, **kwargs):
    """更新系统配置"""
    res = {"msg": None, "code": -1}
    try:
        success = rc.hmset(key, kwargs)
    except Exception, e:
        logger.error(e, exc_info=True)
        res.update(msg="Update system configure error")
    else:
        res.update(code=0 if success else 1)
    return res