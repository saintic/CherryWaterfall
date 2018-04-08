# -*- coding: utf-8 -*-
"""
    CherryWaterfall.views.FrontView
    ~~~~~~~~~~~~~~

    The blueprint for front view.

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os, datetime
from config import GLOBAL, Upyun
from utils.web import login_required, apilogin_required
from utils.Signature import Signature
from utils.upyunstorage import CloudStorage
from utils.tool import logger, md5, gen_rnd_filename, allowed_file, get_current_timestamp, ListEqualSplit, setSystem, timestamp_to_timestring
from werkzeug import secure_filename
from werkzeug.contrib.atom import AtomFeed
from flask import Blueprint, request, g, redirect, make_response, url_for, jsonify, render_template, abort, current_app

# 初始化前台蓝图
FrontBlueprint = Blueprint("front", __name__)
# 初始化签名
sig = Signature()
# 初始化又拍云存储封装接口
api = CloudStorage(timeout=60)

@FrontBlueprint.route("/")
@login_required
def index_view():
    """主页视图"""
    if g.site.get("sys_Close") in ("1", 1):
        return abort(400)
    return render_template("index.html")

@FrontBlueprint.route("/admin/")
@login_required
def admin_view():
    """控制台视图"""
    return render_template("admin.html")

@FrontBlueprint.route('/upload/', methods=['POST','OPTIONS'])
@apilogin_required
@sig.signature_required
def upload_view():
    res = dict(code=-1, msg=None)
    label = request.args.get("label")
    _has_label = lambda label: g.redis.sismember(current_app.config["labelKey"], label) and g.redis.exists("{}:label:{}".format(GLOBAL['ProcessName'], label)) or label == current_app.config["labelDefault"]
    if not label:
        label = current_app.config["labelDefault"]
    if label and _has_label(label):
        f = request.files.get('file')
        if f and allowed_file(f.filename):
            filename = secure_filename(gen_rnd_filename() + "." + f.filename.split('.')[-1]) #随机命名
            basedir = Upyun['basedir'] if Upyun['basedir'].startswith('/') else "/" + Upyun['basedir']
            imgUrl = os.path.join(basedir, filename)
            try:
                upres = api.put(imgUrl, f.stream.read())
            except Exception,e:
                logger.error(e, exc_info=True)
                res.update(code=2, msg="Storage failure")
            else:
                imgId = md5(filename)
                imgUrl = Upyun['dn'].strip("/") + imgUrl
                upres.update(ctime=get_current_timestamp(), imgUrl=imgUrl, imgId=imgId, label=label)
                try:
                    pipe = g.redis.pipeline()
                    pipe.sadd(current_app.config["picKey"], imgId)
                    pipe.hmset("{}:{}".format(GLOBAL['ProcessName'], imgId), upres)
                    pipe.hincrby("{}:label:{}".format(GLOBAL['ProcessName'], label), "imgNum")
                    pipe.execute()
                except Exception,e:
                    logger.error(e, exc_info=True)
                    res.update(code=0, msg="It has been uploaded, but the server has encountered an unknown error")
                else:
                    logger.info("Upload to Upyun file saved, its url is %s, result is %s, imgId is %s" %(imgUrl, upres, imgId))
                    res.update(code=0, imgUrl=imgUrl)
        else:
            res.update(code=1, msg="Unsuccessfully obtained file or format is not allowed")
    else:
        res.update(code=2, msg="Invalid label")
    logger.info(res)
    return jsonify(res)

@FrontBlueprint.route("/api/", methods=['GET', 'POST','OPTIONS', 'DELETE', 'PUT'])
@apilogin_required
@sig.signature_required
def api_view():
    """获取图片数据(以redis为基准)"""
    res = dict(code=-1, msg=None)
    Action = request.args.get("Action")
    # 公共函数
    _get_pics = lambda: [ g.redis.hgetall("{}:{}".format(GLOBAL['ProcessName'], imgId)) for imgId in list(g.redis.smembers(current_app.config["picKey"])) ]
    _get_label = lambda: [ g.redis.hgetall("{}:label:{}".format(GLOBAL['ProcessName'], label)) for label in list(g.redis.smembers(current_app.config["labelKey"])) ]
    _has_label = lambda label: g.redis.sismember(current_app.config["labelKey"], label) and g.redis.exists("{}:label:{}".format(GLOBAL['ProcessName'], label))
    def _set_label(label, user):
        """新建标签"""
        try:
            pipe = g.redis.pipeline()
            pipe.sadd(current_app.config["labelKey"], label)
            pipe.hmset("{}:label:{}".format(GLOBAL['ProcessName'], label), dict(user=user, ctime=get_current_timestamp(), label=label))
            pipe.execute()
        except Exception,e:
            logger.error(e, exc_info=True)
            return False
        else:
            return True
    def _del_label(label):
        """删除标签"""
        imgNum = int(g.redis.hget("{}:label:{}".format(GLOBAL['ProcessName'], label), "imgNum") or 0)
        if imgNum > 0:
            return False
        try:
            pipe = g.redis.pipeline()
            pipe.srem(current_app.config["labelKey"], label)
            pipe.delete("{}:label:{}".format(GLOBAL['ProcessName'], label))
            pipe.execute()
        except Exception,e:
            logger.error(e, exc_info=True)
            return False
        else:
            return True
    # GET请求段
    if request.method == "GET":
        if Action == "getList":
            # 获取图片列表
            sort = request.args.get("sort") or "desc"
            page = request.args.get("page") or 0
            limit = request.args.get("limit") or 10
            label = request.args.get("label")
            # 参数检查
            try:
                page = int(page)
                limit = int(limit)
            except:
                res.update(code=2, msg="Invalid page or limit")
            else:
                data = _get_pics()
                if data:
                    data = sorted(data, key=lambda k:(k.get('ctime',0), k.get('imgUrl',0)), reverse=False if sort == "asc" else True)
                    if label:
                        data = [ i for i in data if i.get("label", current_app.config["labelDefault"]) == label ]
                    count = len(data)
                    data = ListEqualSplit(data, limit)
                    pageCount = len(data)
                    if page < pageCount:
                        res.update(code=0, data=data[page], pageCount=pageCount)
                    else:
                        res.update(code=3, msg="IndexOut with page {}".format(page))
                else:
                    res.update(code=4, msg="No data")
        elif Action == "getInfo":
            # 获取系统相关信息
            data = dict(site=g.site, imageNumber=g.redis.scard(current_app.config["picKey"]))
            res.update(data=data, code=0)
        elif Action == "getOne":
            # 获取随机一张图片
            res.update(data=g.redis.hgetall("{}:{}".format(GLOBAL['ProcessName'], g.redis.srandmember(current_app.config["picKey"]))), code=0)
        elif Action == "getPhoto":
            # 返回相册格式数据
            data = _get_pics()
            res = dict(title=g.site["site_TitleSuffix"], id=1, start=0, data=[ {"alt": timestamp_to_timestring(float(img['ctime'])), "pid": img["imgId"], "src": img["imgUrl"]} for img in sorted(data, key=lambda k:(k.get('ctime',0), k.get('imgUrl',0)), reverse=True) ])
        elif Action == "getLabel":
            # 定义参数
            sort = request.args.get("sort") or "desc"
            try:
                data = _get_label()
                if not data:
                    data = []
                labelDefaultData = g.redis.hgetall("{}:label:{}".format(GLOBAL['ProcessName'], current_app.config["labelDefault"]))
                labelDefaultData.update(label=current_app.config["labelDefault"], user="system", ctime="")
                data.append(labelDefaultData)
                if data and isinstance(data, list):
                    data = [i for i in sorted(data, reverse=False if sort == "asc" else True)]
            except Exception,e:
                logger.error(e, exc_info=True)
                res.update(code=1, msg="Unknown error")
            else:
                res.update(code=0, data=data)
    elif request.method == "POST":
        if Action == "setSystem":
            # 更新系统配置
            data = {k: v for k, v in request.form.iteritems() if k in ("site_TitleSuffix", "site_RssTitle", "site_License", "site_Copyright", "author_Email", "github", "sys_Close", "sso_AllowedUsers", "site_UploadMax", "site_UploadSize")}
            res.update(setSystem(g.redis, current_app.config["sysKey"], **data))
        elif Action == "setLabel":
            label = request.form.get("label")
            if label and not _has_label(label):
                if _set_label(label=label, user=g.uid):
                    res.update(code=0)
                else:
                    res.update(msg="Add label failed", code=5)
            else:
                res.update(msg="Invalid label", code=6)
    elif request.method == "DELETE":
        if Action == "delLabel":
            label = request.form.get("label")
            if label and _has_label(label):
                if _del_label(label):
                    res.update(code=0)
                else:
                    res.update(msg="Del label failed", code=7)
            else:
                res.update(msg="Invalid label", code=8)
    logger.debug(res)
    return jsonify(res)

@FrontBlueprint.route("/feed/")
def feed_view():
    data = [ g.redis.hgetall("{}:{}".format(GLOBAL['ProcessName'], imgId)) for imgId in list(g.redis.smembers(current_app.config["picKey"])) ]
    data = [ i for i in sorted(data, key=lambda k:(k.get('ctime',0), k.get('imgUrl',0)), reverse=True) ][:15]
    feed = AtomFeed(g.site["site_RssTitle"], subtitle='Cherry Blossoms', feed_url=request.url, url=request.url_root, icon=url_for('static', filename='images/favicon.ico', _external=True))
    for img in data:
        title = timestamp_to_timestring(float(img['ctime']))
        content = u'<img src="{}">'.format(img['imgUrl'])
        feed.add(title, content,
                content_type='html',
                id=img['imgId'],
                url=img['imgUrl'],
                updated=datetime.datetime.fromtimestamp(float(img['ctime'])),
                published=datetime.datetime.fromtimestamp(float(img['ctime']))
        )
    return feed.get_response()

