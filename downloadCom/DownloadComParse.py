# -*- coding: utf-8 -*-
__author__ = 'fml'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import time
import os
import re
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
KEYS = [u'url', u'Publisher', u'Publisherwebsite', u'ReleaseDate', u'DateAdded', u'Version',  # Genral
        u'Category', u'Subcategory',  # Category
        u'OperatingSystems', u'AdditionalRequirements',  # Operating Systems
        u'FileSize', u'FileName',  # Download Information
        u'TotalDownloads', u'DownloadsLastWeek',  # Popularity
        u'LicenseModel', u'Limitations', u'Price',  # Pricing
        u'publishersdescription',
        u'userreviews'
        ]
# 判断并新建Data目录,该目录是存放最终的数据
if not os.path.exists('Data'):
    os.makedirs('Data')
# 判断并新建tempData目录，该目录是存放临时文件，如urls
if not os.path.exists('tempData'):
    os.makedirs('tempData')


class DownloadComParse(object):
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
        self.nonerequrls = set()
        self.runflag = False
        self.requrls = set()

    def getUrls(self):
        '''
        获取对应flag的urls
        :return:
        '''
        filename = './tempData/' + 'urlslist_%s_%s' % (self.flag, self.groupid)
        if not os.path.isfile(filename):
            # 需加休眠，不然嵌套太多，会报错
            time.sleep(5)
            return
        with open(filename, 'r') as f:
            lines = map(lambda x: x.strip(), f.readlines())
            for line in lines:
                if line not in self.requrls:
                    self.nonerequrls.add(line)

    def setGroupid(self):
        '''
        动态获取groupid
        :return:
        '''
        return time.strftime('%Y_%m_%d')

    def remove_all_space_char(self, ss):
        """
        去掉所有的不可见字符，包括空格，换行等等
        :param ss:
        :return:
        """
        temp = re.sub(ur'[\x00-\x20]', '', unicode(ss))
        return temp

    def getPageHtml(self, url):
        '''
        获取页面html
        :param url:
        :return:
        '''
        response = None
        response = self.req.get(url, headers=HEADERS)
        if response and hasattr(response, 'status_code') and response.status_code == 200:
            self.requrls.add(url)
            return response

    def parseContent(self, response):
        '''
        解析网页
        :param html:
        :return:
        '''
        html = response.text
        url = response.url
        detail_tree = etree.HTML(html)
        details = detail_tree.xpath('.//*[@class="specs-details"]//tr')
        f = lambda x: x.strip()
        dict_ = dict()
        dict_['url'] = url
        for tail in details:
            if len(tail.xpath('./td')) == 2:
                k = self.remove_all_space_char(''.join(map(f, tail.xpath('./td[1]/text()'))))
                v = ''.join(map(f, tail.xpath('./td[2]//text()')))
                dict_[k] = v.replace(',', '，')
        ft = lambda x: ' '.join(x.split()).strip()
        PublishersDescription = ' '.join(
            filter(lambda x: x, map(ft, detail_tree.xpath(".//*[@id='product-info']//text()")))).replace(
            ',', '，')
        userreviewstree = detail_tree.xpath(".//*[@class='userRateModule'][2]")
        if userreviewstree:
            userreviewstree = userreviewstree[0]
            avrg = ''.join(map(f, userreviewstree.xpath('./a//text()')))
            avrg = str(avrg) if avrg and re.search('\d', avrg) else '0'
            votes = ''.join(userreviewstree.xpath("./p/text()"))
            votes = re.search('(\d+)', votes).group(1) if re.search('(\d+)', votes) else '0'
            stars = ','.join(map(f, userreviewstree.xpath('.//*[@class="percent"]/text()')))
            UserReviews = avrg + ',' + votes + ',' + stars
        else:
            UserReviews = ','.join(['0', '0', '0', '0', '0', '0', '0'])
        dict_['publishersdescription'] = PublishersDescription
        dict_['userreviews'] = UserReviews
        self.save(dict_)

    def save(self, dict_):
        '''
        存储数据
        :param dict_:
        :return:
        '''

        values = map(lambda x: dict_.get(x, ''), KEYS)
        # if len(values) < 4:
        #     return
        vales = ','.join(values)
        filename = './Data/' + 'cownloadcom_%s_%s.csv' % (self.flag, self.groupid)
        with open(filename, 'a') as f:
            f.write(vales.encode('gbk', 'ignore') + '\n')

    def run(self):
        if not self.nonerequrls:
            if self.groupid != self.setGroupid():
                # 重新初试化
                self.groupid = self.setGroupid()
                self.requrls = set()
            self.getUrls()
        if self.nonerequrls:
            url = self.nonerequrls.pop()
            deferToThread(self.getPageHtml, url).addBoth(lambda x: self.parseContent(x))
            reactor.callLater(0.1, self.run)
        else:
            self.run()

    def start(self):
        self.run()
        reactor.run()


if __name__ == '__main__':
    loop = DownloadComParse(flag=sys.argv[1])
    loop.start()
