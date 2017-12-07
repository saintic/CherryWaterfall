# -*- coding: utf-8 -*-
"""
    CherryWaterfall.config
    ~~~~~~~~~~~~~~

    The program configuration file, the preferred configuration item, reads the system environment variable first.

    :copyright: (c) 2017 by Mr.tao.
    :license: MIT, see LICENSE for more details.
"""

import os

GLOBAL={

    "ProcessName": "CherryWaterfall",
    #自定义进程名.

    "Host": os.getenv("cherrywaterfall_host", "0.0.0.0"),
    #监听地址

    "Port": os.getenv("cherrywaterfall_port", 13141),
    #监听端口

    "LogLevel": os.getenv("cherrywaterfall_loglevel", "DEBUG"),
    #应用日志记录级别, 依次为 DEBUG, INFO, WARNING, ERROR, CRITICAL.
}

SSO={

    "SSO.URL": os.getenv("cherrywaterfall_ssourl", "https://passport.saintic.com"),
    #认证中心地址

    "SSO.PROJECT": GLOBAL["ProcessName"],
    #SSO request application.

    "SSO.AllowedUserList": ("taochengwei", )
    #SSO Allowed User List
}

REDIS = os.getenv("cherrywaterfall_redis_url")
# Redis数据库连接信息，格式:
# redis://[:password]@host:port/db
# host,port必填项,如有密码,记得密码前加冒号

#又拍云存储配置
Upyun={
    "bucket": os.getenv("cherrywaterfall_upyun_bucket", ""),
    "username": os.getenv("cherrywaterfall_upyun_username", ""),
    "password": os.getenv("cherrywaterfall_upyun_password", ""),
    "dn": os.getenv("cherrywaterfall_upyun_dn", "https://img.saintic.com"),
    "basedir": os.getenv("cherrywaterfall_upyun_basedir", "/test")
}

#签名配置
Sign={
    "version": os.getenv("cherrywaterfall_sign_version", "v1"),
    "accesskey_id": os.getenv("cherrywaterfall_sign_accesskeyid", "accesskey_id"),
    "accesskey_secret": os.getenv("cherrywaterfall_sign_accesskeysecret", "accesskey_secret"),
}