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

#又拍云存储插件
Upyun={
    "bucket": os.getenv("cherrywaterfall_UpYunStorage_bucket", ""),
    "username": os.getenv("cherrywaterfall_UpYunStorage_username", ""),
    "password": os.getenv("cherrywaterfall_UpYunStorage_password", ""),
    "dn": os.getenv("cherrywaterfall_UpYunStorage_dn", "https://img.saintic.com"),
}