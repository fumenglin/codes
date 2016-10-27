# -*- coding: utf-8 -*-
__author__ = 'fml'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

"""
企业信息网下载模块
"""
import urlparse
import requests
from requests import Request, Session
from requests.cookies import cookiejar_from_dict
import requests.packages.urllib3

requests.packages.urllib3.disable_warnings()
# 忽略请求过程的警告输出
import json
import random
import time
import warnings

from Logging import Log

user_agent = [
    u"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0",
    u"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",
    u"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.10 Chromium/27.0.1453.93 Chrome/27.0.1453.93 Safari/537.36",
    u"Mozilla/5.0 (compatible; WOW64; MSIE 10.0; Windows NT 6.2)",
    u"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Ubuntu/11.10 Chromium/27.0.1453.93 Chrome/27.0.1453.93 Safari/537.36",
]


class RequestObject(object):
    """
    下载模块
    根据requests，Session，自动管理cookie, session保持连接
    外加代理管理模块
    """

    def __init__(self, province_name):
        """
        初始化代理，链接Session，ua
        :return:
        """
        self.ua = random.choice(user_agent)
        self.ss = Session()
        self.pro_name = province_name.lower()
        self.log = Log(self.pro_name)
        self.proxy = None

    def get(self, url, **kwargs):
        """
        封装get请求
        :param url:
        :param kwargs:
        :return:
        """
        t1 = time.time()
        try:
            self.log.info(u'get web url:%s' % url)
            return self.request(url, method='GET', **kwargs)
        except:
            return None
        finally:
            t = time.time() - t1
            self.log.info(u'该次get请求耗时：%d秒' % int(t))

    def post(self, url, **kwargs):
        """
        封装post请求
        :param url:
        :param kwargs:
        :return:
        """
        t1 = time.time()
        try:
            self.log.info(u'post web url:%s,kwargs:%s' % (url, json.dumps(kwargs)))
            return self.request(url, method='POST', **kwargs)
        finally:
            t = time.time() - t1
            self.log.info(u'该次post请求耗时：%d秒' % int(t))

    def request(self, url, method='GET', **kwargs):
        """
        下载模块：Constructs and sends a :class:`Request <Request>`.
        Returns :class:`Response <Response>` object.

        :param method: method for the new :class:`Request` object.
        :param url: URL for the new :class:`Request` object.
        :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
        :param cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
        :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': ('filename', fileobj)}``) for multipart encoding upload.
        :param auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
        :param timeout: (optional) How long to wait for the server to send data
            before giving up, as a float, or a (`connect timeout, read timeout
            <user/advanced.html#timeouts>`_) tuple.
        :type timeout: float or tuple
        :param allow_redirects: (optional) Boolean. Set to True if POST/PUT/DELETE redirect following is allowed.
        :type allow_redirects: bool
        :param proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        :param verify: (optional) if ``True``, the SSL cert will be verified. A CA_BUNDLE path can also be provided.
        :param stream: (optional) if ``False``, the response content will be immediately downloaded.
        :param cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
        """

        def _get_values(strs, default=None):
            return kwargs[strs] if strs in kwargs else default

        params = _get_values('params', default=None)
        data = _get_values('data')
        headers = kwargs['headers'] if 'headers' in kwargs else {"Host": urlparse.urlparse(url).netloc,
                                                                 "User-Agent": self.ua}
        ua = _get_values('ua', default=None)
        if ua:
            headers.update({"User-Agent": ua})
        verify = _get_values('verify', default=False)
        stream = _get_values('stream', default=False)
        cert = _get_values('cert', default=None)
        timeout = _get_values('timeout', default=120)
        allow_redirects = _get_values('allow_redirects', default=True)
        _retry = _get_values('retry') or 5
        while _retry:
            _retry -= 1
            try:
                self.log.info(u"使用代理 %s" % self.proxy)
                req = Request(method.upper(),
                              url,
                              data=data or {},
                              headers=headers or {},
                              params=params or {}
                              )
                prepped = self.ss.prepare_request(req)
                proxies = {'http': 'http://' + self.proxy, 'https': 'http://' + self.proxy} if self.proxy else {}
                settings = self.ss.merge_environment_settings(prepped.url, proxies, stream, verify, cert)
                send_kwargs = {
                    'timeout': timeout,
                    'allow_redirects': allow_redirects,
                }
                send_kwargs.update(settings)
                resp = self.ss.send(prepped,
                                    **send_kwargs
                                    )
                if resp and isinstance(resp, object) and resp.status_code == requests.codes.ok:
                    return resp
                else:
                    if 500 <= resp.status_code < 600:  # 返回code为500和600之间时候是服务器的问题，故休眠1分钟
                        self.log.info(u'返回码为%d，休眠一分钟' % resp.status_code)
                        time.sleep(60)
                    resp.raise_for_status()
            except Exception as e:
                self.log.error(u"获取页面内容异常：%s" % (e))
        raise Exception(u'%s获取页面失败！' % url)


if __name__ == '__main__':
    pass
