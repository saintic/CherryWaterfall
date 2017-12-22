# -*- coding: utf-8 -*-
"""
    UploadDemo.main
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

import os, datetime, random
from werkzeug import secure_filename
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for

#文件上传存放的文件夹, 值为非绝对路径时，相对于项目根目录
IMAGE_FOLDER  = 'static/upload/'
#生成无重复随机数
gen_rnd_filename = lambda :"%s%s" %(datetime.datetime.now().strftime('%Y%m%d%H%M%S'), str(random.randrange(1000, 10000)))
#文件名合法性验证
allowed_file = lambda filename: '.' in filename and filename.rsplit('.', 1)[1] in set(['png', 'jpg', 'jpeg', 'gif', 'bmp'])

app = Flask(__name__)
app.config.update(
    SECRET_KEY = os.urandom(24),
    # 上传文件夹
    UPLOAD_FOLDER = os.path.join(app.root_path, IMAGE_FOLDER),
    # 最大上传大小，当前16MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
)

@app.route("/")
def index_view():
    """主页视图"""
    return render_template("index.html")

@app.route('/showimg/<filename>')
def showimg_view(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload/', methods=['POST','OPTIONS'])
def upload_view():
    res = dict(code=-1, msg=None)
    f = request.files.get('file')
    if f and allowed_file(f.filename):
        filename = secure_filename(gen_rnd_filename() + "." + f.filename.split('.')[-1]) #随机命名
        # 自动创建上传文件夹
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        # 保存图片
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imgUrl = url_for('showimg_view', filename=filename, _external=True)
        res.update(code=0, data=dict(src=imgUrl))
    else:
        res.update(msg="Unsuccessfully obtained file or format is not allowed")
    return jsonify(res)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)