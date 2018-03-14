# -*- coding: utf-8 -*-
"""
    CherryWaterfall.main
    ~~~~~~~~~~~~~~

    Entrance

    Docstring conventions:
    http://flask.pocoo.org/docs/0.10/styleguide/#docstrings

    Comments:
    http://flask.pocoo.org/docs/0.10/styleguide/#comments

    :copyright: (c) 2017 by staugur.
    :license: MIT, see LICENSE for more details.
"""

import os
import sys
import jinja2
from config import GLOBAL, REDIS, SYSTEM
from version import __version__
from utils.tool import err_logger, access_logger, getSystem
from utils.web import verify_sessionId, analysis_sessionId, get_redirect_url
from libs.plugins import PluginManager
from views import FrontBlueprint
from redis import from_url
from flask import Flask, request, g, jsonify, send_from_directory
reload(sys)
sys.setdefaultencoding('utf-8')

__author__ = 'staugur'
__email__ = 'staugur@saintic.com'
__date__ = "2017-12-05"
__doc__ = 'Waterfall Stream Picture Station'

#又拍云存储图片数据缓存
picKey = "{}:Images".format(GLOBAL["ProcessName"])
#系统配置
sysKey = "{}:System".format(GLOBAL["ProcessName"])
#标签索引
labelKey = "{}:labels".format(GLOBAL['ProcessName'])
labelDefault = u"未分类"

# 初始化定义application
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.urandom(24),
    picKey=picKey,
    sysKey=sysKey,
    labelKey=labelKey,
    labelDefault=labelDefault
)

# 初始化插件管理器(自动扫描并加载运行)
plugin = PluginManager()

# 注册多模板文件夹
loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader([p.get("plugin_tpl_path") for p in plugin.get_enabled_plugins if os.path.isdir(os.path.join(app.root_path, p["plugin_tpl_path"]))]),
])
app.jinja_loader = loader

# 注册全局模板扩展点
for tep_name, tep_func in plugin.get_all_tep.iteritems():
    app.add_template_global(tep_func, tep_name)

# 注册蓝图扩展点
for bep in plugin.get_all_bep:
    prefix = bep["prefix"]
    app.register_blueprint(bep["blueprint"], url_prefix=prefix)

# 注册视图包中蓝图
app.register_blueprint(FrontBlueprint)

# 添加模板上下文变量
@app.context_processor
def GlobalTemplateVariables():
    data = {"Version": __version__, "Author": __author__, "Email": __email__, "Doc": __doc__, "Sign": SYSTEM["Sign"], "picKey": picKey, "labelDefault": labelDefault}
    return data


@app.before_request
def before_request():
    g.signin = verify_sessionId(request.cookies.get("sessionId"))
    g.uid = analysis_sessionId(request.cookies.get("sessionId")).get("uid") if g.signin else None
    g.redis = from_url(REDIS)
    g.site = getSystem(g.redis, sysKey)["data"]
    # 仅是重定向页面快捷定义
    g.redirect_uri = get_redirect_url()
    # 上下文扩展点之请求后(返回前)
    before_request_hook = plugin.get_all_cep.get("before_request_hook")
    for cep_func in before_request_hook():
        cep_func(request=request, g=g)


@app.after_request
def after_request(response):
    data = {
        "status_code": response.status_code,
        "method": request.method,
        "ip": request.headers.get('X-Real-Ip', request.remote_addr),
        "url": request.url,
        "referer": request.headers.get('Referer'),
        "agent": request.headers.get("User-Agent")
    }
    access_logger.info(data)
    # 上下文扩展点之请求后(返回前)
    after_request_hook = plugin.get_all_cep.get("after_request_hook")
    for cep_func in after_request_hook():
        cep_func(request=request, response=response, data=data)
    return response


@app.teardown_request
def teardown_request(exception):
    if exception:
        err_logger.error(exception, exc_info=True)
    if hasattr(g, "redis"):
        g.redis.connection_pool.disconnect()


@app.errorhandler(500)
def server_error(error=None):
    if error:
        err_logger.error("500: {}".format(error), exc_info=True)
    message = {
        "msg": "Server Error",
        "code": 500
    }
    return jsonify(message), 500


@app.errorhandler(404)
def not_found(error=None):
    if error:
        err_logger.info("404: {}".format(error))
    message = {
        'code': 404,
        'msg': 'Not Found: ' + request.url,
    }
    return jsonify(message), 404


@app.errorhandler(403)
def Permission_denied(error=None):
    message = {
        "msg": "Authentication failed, permission denied.",
        "code": 403
    }
    return jsonify(message), 403


@app.route('/favicon.ico')
def favicon():
    #添加一条指向站点图标的路由
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(host=GLOBAL["Host"], port=int(GLOBAL["Port"]), debug=True)
