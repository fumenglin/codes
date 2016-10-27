# -*- coding: utf-8 -*-
__author__ = 'fml'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import time
import re
import os
import socket

socket.setdefaulttimeout(180)
from twisted.internet import reactor

reactor.suggestThreadPoolSize(200000)
from twisted.internet.threads import deferToThread

from lxml import etree

sys.path.append('./util')
from util.Request import RequestObject
from util.Logging import Log

FLAGS = ['windows', 'mac', 'ios', 'android']
GROUPID = time.strftime('%Y_%m_%d')
HEADERS = {
    'Host': 'download.cnet.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate'
}
# 判断并新建tempData目录，该目录是存放临时文件，如urls
if not os.path.exists('tempData'):
    os.makedirs('tempData')


class DownloadComUrls(object):
    def __init__(self, flag=None, groupid=GROUPID):
        '''
        :param flag: 标志，eg: one of 'windows', 'mac', 'ios', 'android'
        :param groupid: 类似于kafka里的group id ,便于获取数据
        '''
        self.flag = flag
        if self.flag not in FLAGS:
            raise Exception(u'抓取内容错误，错误标志为：%s,正确的应为%s中的一个' % (self.flag, '\t'.join(FLAGS)))
        self.groupid = groupid
        self.req = RequestObject(self.flag + self.groupid)
        self.log = Log(self.flag + self.groupid)
        self.pageurls = list()
        self.runflag = False

    def setUrl(self, page=None):
        '''
        获取url
        :return:
        '''
        if page:
            return 'http://download.cnet.com/s/software/%s/?sort=most-popular&page=%d' % (self.flag, int(page))
        return 'http://download.cnet.com/most-popular/%s/' % self.flag

    def setGroupid(self):
        '''
        动态获取groupid
        :return:
        '''
        return time.strftime('%Y_%m_%d')

    def getPageHtml(self, url):
        '''
        获取页面html
        :param url:
        :return:
        '''
        html = self.req.get(url, headers=HEADERS)
        return html

    def parsePageHtml(self, response):
        '''
        解析页面urls 或者总页数
        :param html:
        :return:
        '''
        page_tree = etree.HTML(response.text)
        f = lambda x: x.strip()
        urls = map(f, page_tree.xpath('.//*[@class="item-anchor"]/@href'))
        map(self.save, urls)

    def getPageUrls(self, html):
        '''
        获取总的页面URLS
        :return:
        '''
        page_tree = etree.HTML(html.text)
        results_total = ''.join(page_tree.xpath(".//*[@class='results-total']/text()")).strip()
        results_total_int = int(''.join(re.findall('(\d*)', results_total)))
        self.pageurls.extend([self.setUrl(page=x) for x in range(2, results_total_int // 10 + 1)])

    def save(self, data):
        '''
        存储数据
        :param data:
        :return:
        '''
        filename = './tempData/' + 'urlslist_%s_%s' % (self.flag, self.groupid)
        with open(filename, 'a') as f:
            f.write(data + '\n')

    def run(self):
        if not self.pageurls and self.runflag == False:
            homeurl = self.setUrl()
            homepage = self.getPageHtml(homeurl)
            self.parsePageHtml(homepage)
            self.getPageUrls(homepage)
            self.runflag = True
        if not self.pageurls and self.runflag == True:
            if self.groupid != self.setGroupid():
                self.groupid = self.setGroupid()
                self.runflag = False
                self.run()
            else:
                return
        url = self.pageurls.pop()
        deferToThread(self.getPageHtml, url).addCallback(lambda x: self.parsePageHtml(x))
        reactor.callLater(0.1, self.run)

    def start(self):
        self.run()
        reactor.run()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        flag = sys.argv[1]
    else:
        flag = 'windows'
    loop = DownloadComUrls(flag=flag)
    loop.start()
