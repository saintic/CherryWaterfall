#-*- coding:utf-8 -*-

__doc__     = "Splice, Split and Modify URL"
__date__    = '2016-11-10'
__author__  = "Mr.tao <staugur@saintic.com>"
__version__ = '1.2'
__license__ = 'MIT'

import re
import urllib
from urlparse import urlunparse, urlparse
from posixpath import normpath
from os.path import join as urljoin

class ArgError(Exception):
    pass

class Splice(object):
    """
    拼接URL，参数顺序为scheme, netloc, port, path, params, query, fragment
    其中netloc为必须参数
    """
    def __init__(self, scheme='http', netloc=None, port=None, path='/', params=None, query=None, fragment=None):
        if not netloc:
            raise ArgError("Not netloc")
        if port in (80, None) and scheme == "http":
            self.netloc = netloc
        elif port in (443, None) and scheme == "https":
            self.netloc = netloc
        else:
            self.netloc = "%s:%s" %(netloc, port)
        if query:
            if isinstance(query, dict):
                self.query = urllib.urlencode(query)
            elif isinstance(query, str):
                self.query = query
            else:
                raise TypeError("query is string or dict")
        else:
            self.query= ''
        self.scheme   = scheme
        self.path     = path
        self.params   = params
        self.fragment = fragment

    def do(self):
        "run it, you can get a good stitching of the complete URL."
        return urlunparse((self.scheme, self.netloc, self.path, self.params, self.query, self.fragment))

    @property
    def geturl(self):
        "Equivalent class properties of the `do` function"
        return self.do()

    def __unicode__(self):
        return "Splice URL for SaintIC ULR Project."


class Split(object):
    """拆分URL，参数为url，返回元组，顺序为scheme, netloc, path, params, query, fragment"""

    def __init__(self, url):
        if not "http://" in url and not "https://" in url:
            raise ArgError("A url is not complete, the lack of HTTP protocol")
        self.url = url

    def do(self):
        "run it, you can get a tuple for (scheme, netloc, path, params, query, fragment)"
        _PR = urlparse(self.url)
        return _PR.scheme, _PR.netloc, _PR.path, _PR.params, _PR.query, _PR.fragment

    def __unicode__(self):
        return "Split URL for SaintIC ULR Project."


class Modify(object):
    """
    修改URL，为ULR项目开设的组件，传入一个url和dict查询字典，组成成新url返回。
    典型的应用场景是Web应用接受登录注册请求访问ULR控制，操作完后跳转到新URL，这个新URL带有额外查询参数。
    """

    def __init__(self, url, path=None, query=None):
        if not "http://" in url and not "https://" in url:
            raise ArgError("A url is not complete, the lack of HTTP protocol")
        self.url = url
        self.path = path
        self.query = query

    def do(self):
        "run it, get a new url"
        scheme, netloc, path, params, query, fragment = Split(self.url).do()

        if isinstance(self.query, dict):
            query = query + "&" + urllib.urlencode(self.query) if query else urllib.urlencode(self.query)

        path = urljoin(path, self.path).replace('\\', '/') if self.path else path
        
        return Splice(scheme=scheme, netloc=netloc, path=path, params=params, query=query, fragment=fragment).geturl

    @property
    def geturl(self):
        "Equivalent class properties of the `do` function"
        return self.do()
