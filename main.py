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

import datetime, SpliceURL, os, json, sys, logging
from config import GLOBAL, Upyun, REDIS, Sign
from utils.Signature import Signature
from utils.upyunstorage import CloudStorage
from utils.tool import md5, gen_rnd_filename, allowed_file, login_required, get_current_timestamp, ListEqualSplit, getSystem, setSystem, timestamp_datetime, comma_pat
from redis import from_url
from werkzeug import secure_filename
from werkzeug.contrib.atom import AtomFeed
from flask import Flask, request, g, redirect, make_response, url_for, jsonify, render_template, abort, send_from_directory
reload(sys)
sys.setdefaultencoding('utf-8')

#初始化定义application
app = Flask(__name__)
#签名
sig = Signature()
#又拍云存储封装接口
api = CloudStorage()
#又拍云存储图片数据缓存
picKey = "{}:Images".format(GLOBAL["ProcessName"])
#系统配置
sysKey = "{}:System".format(GLOBAL["ProcessName"])

# 添加模板上下文变量
@app.context_processor  
def GlobalTemplateVariables():  
    data = {"Sign": Sign, "picKey": picKey}
    return data

@app.before_request
def before_request():
    g.sessionId = request.cookies.get("sessionId", "")
    g.username = request.cookies.get("username", "")
    g.expires = request.cookies.get("time", "")
    g.signin = True
    g.redis = from_url(REDIS)
    g.site = getSystem(g.redis, sysKey)["data"]

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
    logging.info(data)
    return response

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, "redis"):
        g.redis.connection_pool.disconnect()

@app.route('/favicon.ico')
def favicon():
    #添加一条指向站点图标的路由
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/")
@login_required
def index_view():
    """主页视图"""
    if g.site.get("sys_Close") in ("1", 1):
        return abort(400)
    return render_template("index.html")

@app.route("/admin/")
@login_required
def admin_view():
    """控制台视图"""
    return render_template("admin.html")

@app.route('/upload/', methods=['POST','OPTIONS'])
@login_required
@sig.signature_required
def upload_view():
    res = dict(code=-1, msg=None)
    logging.debug(request.files)
    f = request.files.get('file')
    if f and allowed_file(f.filename):
        filename = secure_filename(gen_rnd_filename() + "." + f.filename.split('.')[-1]) #随机命名
        basedir = Upyun['basedir'] if Upyun['basedir'].startswith('/') else "/" + Upyun['basedir']
        imgUrl = os.path.join(basedir, filename)
        try:
            upres = api.put(imgUrl, f.stream.read())
        except Exception,e:
            logging.error(e, exc_info=True)
            res.update(code=2, msg="Storage failure")
        else:
            imgId = md5(filename)
            imgUrl = Upyun['dn'].strip("/") + imgUrl
            upres.update(ctime=get_current_timestamp(), imgUrl=imgUrl, imgId=imgId)
            try:
                pipe = g.redis.pipeline()
                pipe.sadd(picKey, imgId)
                pipe.hmset("{}:{}".format(GLOBAL['ProcessName'], imgId), upres)
                pipe.execute()
            except Exception,e:
                logging.error(e, exc_info=True)
                res.update(code=0, msg="It has been uploaded, but the server has encountered an unknown error")
            else:
                logging.info("Upload to Upyun file saved, its url is %s, result is %s, imgId is %s" %(imgUrl, upres, imgId))
                res.update(code=0, imgUrl=imgUrl)
    else:
        res.update(code=1, msg="Unsuccessfully obtained file or format is not allowed")
    logging.info(res)
    return jsonify(res)

@app.route("/api/", methods=['GET', 'POST','OPTIONS'])
@sig.signature_required
def api_view():
    """获取图片数据(以redis为基准)"""
    res = dict(code=-1, msg=None)
    Action = request.args.get("Action")
    # GET请求段
    if request.method == "GET":
        if Action == "getList":
            # 获取图片列表
            sort = request.args.get("sort") or "desc"
            page = request.args.get("page") or 0
            length = request.args.get("length") or 10
            # 参数检查
            try:
                page = int(page)
                length = int(length)
            except:
                res.update(code=2, msg="Invalid page or length")
            else:
                data = [ g.redis.hgetall("{}:{}".format(GLOBAL['ProcessName'], imgId)) for imgId in list(g.redis.smembers(picKey)) ]
                if data:
                    data = [ i for i in sorted(data, key=lambda k:(k.get('ctime',0), k.get('imgUrl',0)), reverse=False if sort == "asc" else True) ]
                    data = ListEqualSplit(data, length)
                    pageCount = len(data)
                    if page < pageCount:
                        res.update(code=0, data=data[page], pageCount=pageCount, page=page, length=length)
                    else:
                        res.update(code=3, msg="IndexOut with page {}".format(page))
                else:
                    res.update(code=4, msg="No data")
        elif Action == "getInfo":
            # 获取SAE应用信息
            sae = dict(APP_NAME=os.getenv("APP_NAME"), APP_VERSION=os.getenv("APP_VERSION"), PORT=os.getenv("POST"))
            # 获取系统相关信息
            data = dict(site=g.site, imageNumber=g.redis.scard(picKey), sae=sae)
            res.update(data=data, code=0)
        elif Action == "getOne":
            # 获取随机一张图片
            res.update(data=g.redis.hgetall("{}:{}".format(GLOBAL['ProcessName'], g.redis.srandmember(picKey))), code=0)
    elif request.method == "POST":
        if Action == "setSystem":
            # 更新系统配置
            data = {k: v for k, v in request.form.iteritems() if k in ("site_TitleSuffix", "site_RssTitle", "site_License", "site_Copyright", "author_Email", "github", "sys_Close", "site_UploadMax")}
            res.update(setSystem(g.redis, sysKey, **data))
    logging.debug(res)
    return jsonify(res)

@app.route("/feed/")
def feed_view():
    data = [ g.redis.hgetall("{}:{}".format(GLOBAL['ProcessName'], imgId)) for imgId in list(g.redis.smembers(picKey)) ]
    data = [ i for i in sorted(data, key=lambda k:(k.get('ctime',0), k.get('imgUrl',0)), reverse=True) ][:15]
    feed = AtomFeed(g.site["site_RssTitle"], subtitle='Cherry Blossoms', feed_url=request.url, url=request.url_root, icon=url_for('static', filename='images/favicon.ico', _external=True), author=__author__)
    for img in data:
        title = timestamp_datetime(float(img['ctime']))
        content = u'<img src="{}">'.format(img['imgUrl'])
        feed.add(title, content,
                content_type='html',
                id=img['imgId'],
                url=img['imgUrl'],
                author=__author__,
                updated=datetime.datetime.fromtimestamp(float(img['ctime'])),
                published=datetime.datetime.fromtimestamp(float(img['ctime']))
        )
    return feed.get_response()

if __name__ == '__main__':
    Host  = GLOBAL.get('Host')
    Port  = GLOBAL.get('Port')
    app.run(host=Host, port=int(Port), debug=True)