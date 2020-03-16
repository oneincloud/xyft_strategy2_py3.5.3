'''
皇家彩世界官网
https://www.1396r.com/
'''
import time
import datetime
from dateutil.parser import parse
import os
import copy
import logging
import random
from bs4 import BeautifulSoup
from commlib.xyftlib.grabs.grab_base import GrabBase

class GrabHuangjia(GrabBase):

    def __init__(self):
        '''
        网站平台构造器
        '''
        self.website = "皇家彩世界官网"
        self.domain = "https://www.1396r.com/"
        # self.domain = "https://www.1396rfdsafdsaoglkjfdsafds.com/"
        self.startAt = datetime.date(2007, 1, 1)

        print("普通爬虫实例构造器：皇家彩世界官网")
        print("网站：%s" % self.website)

        GrabBase.__init__(self)

    def fetch_get(self,date):
        '''
        爬取一天数据实现（子类必需实现的方法）
        :param date:
        :return:
        '''
        print("爬取一天记录数据:%s" % date)

        records = None

        # 构造URL
        url = "%sxyft/kaijiang?date=%s&_=%d" % (self.domain, date, int(time.time() * 1000))
        _headers = copy.deepcopy(self.ajax_headers)
        _headers['Referer'] = 'https://www.1396r.com/xyft/kaijiang'

        try:

            response = self.clientSession.get(url,headers=_headers,timeout=20)


            if response.status_code == 200:
                # 分析提取记录
                records = self.fetch_parse(html=response.text)
        except Exception as e:
            print(e)
            records = None

        return records

    def fetch_parse(self,html):
        '''
        解悉处理响爬取响应内容（子类必需实现的方法）
        :param html:
        :return: 返回格式[
                            [期数,开奖时间,num1,num2,num3,num4,num5,num6,num7,num8,num9,num10]
                            [issue,open_at,r{1~10}]
                        ]
        '''
        # print("解悉处理响爬取响应内容")

        records = []

        soup = BeautifulSoup(html,'html.parser')

        allTr = soup.find_all('tr')

        for tr in allTr:
            tds = tr.find_all('td')

            record = []

            # 期数、时间
            iTags = tds[0].find_all("i")
            i1 = str(iTags[0].text).strip()
            i2 = str(iTags[1].text).strip()

            i1 = i1.split("-")

            awardTime = parse(" ".join([i1[0], i2])).strftime("%Y-%m-%d %H:%M:%S")
            period = int(i1[0] + str(int(i1[1])).zfill(3))

            record.append(period)
            record.append(awardTime)

            # 开奖号码
            for span in tds[1].find_all("span"):
                record.append(int(span.text))

            records.append(record)

        return records




