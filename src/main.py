# -*- coding: utf-8 -*-
"""
    CherryWaterfall.main
    ~~~~~~~~~~~~~~

    This is an entry files, main applications, and some initialization operations.

    Docstring conventions:
    http://flask.pocoo.org/docs/0.10/styleguide/#docstrings

    Comments:
    http://flask.pocoo.org/docs/0.10/styleguide/#comments

    :copyright: (c) 2017 by Mr.tao.
    :license: MIT, see LICENSE for more details.
"""

__author__  = "Mr.tao"
__email__   = "staugur@saintic.com"
__date__    = "2017-12-05"

import datetime, SpliceURL
from config import GLOBAL, SSO, Upyun
from thirds.binbase64 import base64str
from utils.Signature import Signature
from utils.tool import logger, isLogged_in, md5, gen_rnd_filename, UploadImage2Upyun, allowed_file, login_required
from werkzeug import secure_filename
from flask import Flask, request, g, redirect, make_response, url_for, jsonify, render_template

#初始化定义application
app = Flask(__name__)
#签名
sig = Signature()

@app.before_request
def before_request():
    g.sessionId = request.cookies.get("sessionId", "")
    g.username  = request.cookies.get("username", "")
    g.expires   = request.cookies.get("time", "")
    g.signin    = isLogged_in('.'.join([ g.username, g.expires, g.sessionId ]))

@app.after_request
def after_request(response):
    data = {
        "status_code": response.status_code,
        "method": request.method,
        "ip": request.headers.get('X-Real-Ip', request.remote_addr),
        "url": request.url,
        "referer": request.headers.get('Referer'),
        "agent": request.headers.get("User-Agent"),
    }
    logger.info(data)
    #response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route('/login/')
def login():
    if g.signin:
        return redirect(url_for("index"))
    else:
        query = {"sso": True,
           "sso_r": SpliceURL.Modify(request.url_root, "/sso/").geturl,
           "sso_p": SSO["SSO.PROJECT"],
           "sso_t": md5("%s:%s" %(SSO["SSO.PROJECT"], SpliceURL.Modify(request.url_root, "/sso/").geturl))
        }
        SSOLoginURL = SpliceURL.Modify(url=SSO["SSO.URL"], path="/login/", query=query).geturl
        logger.info("User request login to SSO: %s" %SSOLoginURL)
        return redirect(SSOLoginURL)

@app.route('/logout/')
def logout():
    SSOLogoutURL = SSO.get("SSO.URL") + "/sso/?nextUrl=" + request.url_root.strip("/")
    resp = make_response(redirect(SSOLogoutURL))
    resp.set_cookie(key='logged_in', value='', expires=0)
    resp.set_cookie(key='username',  value='', expires=0)
    resp.set_cookie(key='sessionId',  value='', expires=0)
    resp.set_cookie(key='time',  value='', expires=0)
    resp.set_cookie(key='Azone',  value='', expires=0)
    return resp

@app.route('/sso/')
def sso():
    ticket = request.args.get("ticket")
    if not ticket:
        logger.info("sso ticket get failed")
        return """<html><head><title>正在跳转中……</title><meta http-equiv="Content-Language" content="zh-CN"><meta HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=utf8"><meta http-equiv="refresh" content="1.0;url={}"></head><body></b>用户未授权, 返回登录, 请重新认证!<b></body></html>""".format(url_for("logout"))
    logger.info("ticket: %s" %ticket)
    username, expires, sessionId = ticket.split('.')
    if username and not username in SSO["SSO.AllowedUserList"]:
        logger.info("BlueSky is not allowed to login with {}.".format(username))
        return redirect(url_for("sso"))
    if expires == 'None':
        UnixExpires = None
    else:
        UnixExpires = datetime.datetime.strptime(expires,"%Y-%m-%d")
    resp = make_response(redirect(url_for("index")))
    resp.set_cookie(key='logged_in', value="yes", expires=UnixExpires)
    resp.set_cookie(key='username',  value=username, expires=UnixExpires)
    resp.set_cookie(key='sessionId', value=sessionId, expires=UnixExpires)
    resp.set_cookie(key='time', value=expires, expires=UnixExpires)
    resp.set_cookie(key='Azone', value="sso", expires=UnixExpires)
    return resp

@app.route("/")
#@sig.signature_required
@login_required
def index():
    return render_template("admin.html")

@app.route("/admin")
@sig.signature_required
@login_required
def admin():
    return render_template("admin.html")

@app.route('/upload/', methods=['POST','OPTIONS'])
@sig.signature_required
@login_required
def upload():
    logger.debug(request.files)
    f = request.files.get('file')
    if f and allowed_file(f.filename):
        filename = secure_filename(gen_rnd_filename() + "." + f.filename.split('.')[-1]) #随机命名
        imgUrl = u"/{}/{}".format(GLOBAL["ProcessName"], filename)
        upres  = UploadImage2Upyun(imgUrl, f.stream.read())
        imgUrl = Upyun['dn'].strip("/") + imgUrl
        logger.info("Upload to Upyun file saved, its url is %s, result is %s" %(imgUrl, upres))
        res = dict(code=0, imgUrl=imgUrl)
    else:
        res = dict(code=1, msg=u"上传失败: 未成功获取文件或格式不允许")
    logger.info(res)
    return jsonify(res)

if __name__ == '__main__':
    Host  = GLOBAL.get('Host')
    Port  = GLOBAL.get('Port')
    app.run(host=Host, port=int(Port), debug=True)