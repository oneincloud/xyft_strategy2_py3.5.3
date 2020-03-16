'''
异步爬虫基类
'''
import os
import datetime
import time
import copy
import requests
from functools import partial
from dateutil.parser import parse
from dateutil import rrule
import pandas as pd
import numpy as np

class GrabBase():

    max_threads = 10               # 爬虫最大线程数

    dailyStartAt = '13:10'         # 每天起始开奖时间
    dailyStartAtInt = 1310         # 每天结束开奖时间
    dailyEndAt = '04:05'
    dailyEndAtInt = 405
    openInterval = 5 * 60           # 开奖间隔，单位（秒）

    website = ''
    domain = None
    startAt = datetime.date(2019, 2, 3)

    headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'zh-CN,zh;q=0.9'
    }

    ajax_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    def __init__(self,startAt=None,domain=None,headers=None):
        '''
        普通爬虫基类（构造器）
        :param startAt:
        :param domain:
        :param headers:
        '''
        print('[-------------------普通爬虫基类（构造器）-------------------]')

        self.clientSession = None

    def getSession(self):
        '''
        初始化session对象
        :return:
        '''
        if self.clientSession is not None:
            return self.clientSession

        # 初始化session会话处理，如果继续为实现了initSession方法，则调用子类初始化
        _method = "initSession"

        if callable(getattr(self,_method,None)) == False:
            _method = "_GrabBase__initSession"

        getattr(self,_method)()


        return self.clientSession

    def __initSession(self):
        '''
        使用基类方法初始化Session
        :return:
        '''
        print("使用基类方法初始化Session")
        try:
            self.clientSession = requests.Session()
            self.clientSession.headers.update(self.headers)

            self.clientSession.get(self.domain,timeout=30)

        except Exception as e:
            print(e)
            # self.clientSession = None
        return self.clientSession


    def loadDay(self,date = None):
        '''
        加载1日数据
        :param date:
        :return:
        '''
        self.getSession()

        if date is None:
            date = self.todayDate()

        records = self.fetch_get(date)

        return records

    def loadAll(self,startAt = None,endAt = None):
        '''
        爬取全部或指定范围的数据
        :param startAt:
        :param endAt:
        :return:
        '''
        print("爬取全部或指定范围的数据")
        self.getSession()
        dateList = self.dateRange(startAt, endAt)

        print("即将开始任务，计划总任务数：%d" % len(dateList))

        maxTest = len(dateList) // 5 + 20
        currentTest = 0
        resultFaild = copy.deepcopy(dateList)

        result = {}

        while len(resultFaild) > 0 and maxTest > 0:

            newResultFaild = []

            for date in resultFaild:
                records = self.fetch_get(date)
                if records is not None:
                    result[date] = records
                else:
                    newResultFaild.append(date)

            maxTest -= 1
            currentTest += 1

            if len(newResultFaild) == 0:
                break   # 没有错误返回

            # 获取错误的任务列表
            resultFaild = copy.deepcopy(newResultFaild)
            print("存在错误的获取数量%d，【%d/%d】 次2秒后将重试失败任务，" % (len(resultFaild), currentTest, maxTest))
            time.sleep(2)

        return result

    def toDataFrame(self,records):
        '''
        将爬取的结果转换为Pandas的DataFrame类型
        :param records:
        :return:
        '''
        alllist = []
        if isinstance(records,list):
            alllist = records
        elif isinstance(records,dict):
            for daliy in records.values():
                if isinstance(daliy, list):
                    alllist.extend(daliy)

        columns = ['issue','open_at'] + ['r'+str(i+1) for i in range(10)]
        df = pd.DataFrame(alllist,columns=columns)

        # 设置数据类型
        df['issue'] = df['issue'].astype(np.int64)
        df['open_at'] = df['open_at'].astype(np.datetime64)
        for i in range(1,11):
            r = 'r'+str(i)
            df[r] = df[r].astype(np.int)

        return df


    def toList(self,records,ascending = True):
        '''
        将爬取的结果转换为列表
        :param results:
        :param ascending:  排序方式，True倒序，Fasle顺序
        :return:
        '''
        df = None
        if isinstance(df,pd.DataFrame) == False:
            df = self.toDataFrame(records)
        else:
            df = records.copy(deep=True)

        df.sort_values(by='issue',ascending=ascending,inplace=True)
        return df.values.tolist()

    def saveTo(self,records,fname=None,fpath=None,ext='xls'):
        '''
        将数据保存到CSV文件
        :param records:
        :param fname:       空时自动生成文件名，可以填写相对路径或绝对路径
        :param fpath:       可指定保存目录，当文件名为None时，自动生成文件名
        :return:
        '''
        if isinstance(records,pd.DataFrame) == False:
            records = self.toDataFrame(records)

        if ext is None:
            ext = 'xlsx'
        ext = str(ext).strip()

        if ext not in ['xls','xlsx','csv']:
            ext = 'xlsx'

        fileName = self.getFileName(fname=fname, fpath=fpath, prefix='开奖记录_',ext=ext)

        try:
            # 常试创建目录
            fpath,fname = os.path.split(fileName)
            if not os.path.exists(fpath):
                os.makedirs(fpath)

            if ext == 'csv':
                records.to_csv(fileName,index=False)
            else:
                records.to_excel(fileName,index=False)

            print("保存文件：%s" % fileName)
        except Exception as e:
            print(e)
            fileName = None

        return fileName

    def getFileName(self,fname=None,fpath=None,prefix="",ext="xls"):
        '''
        生成有效的文件名
        :param fname:
        :param fpath:
        :param prefix:
        :param ext:
        :return:
        '''
        # print("fname=%s" % fname)
        # print("fpath=%s" % fpath)

        fullName = None

        if fpath is None:
            fpath = os.getcwd()

        if fname is not None:
            if os.path.isabs(fname):
                fullName = fname
            else:
                fullName = os.path.sep.join([fpath, fname])

        if ext.startswith(".") == False:
            ext = '.' + ext

        if fullName is None:
            # 自动生成文件名
            # fname = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + '.csv'
            fname = ''.join([prefix,datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),ext])
            fullName = os.path.sep.join([fpath, fname])

        if os.path.isabs(fullName) == False:
            fullName = os.path.sep.join([os.getcwd(), fullName])

        # fpath, fname = os.path.split(fullName)

        # print("fname=%s" % fname)
        # print("fpath=%s" % fpath)
        # print("funllName=%s" % fullName)


        return fullName

    def resultOfLoadAll(self,records,tasks = None):
        '''
        分析结果集
        :param records:
        :return:
        '''
        all = len(records)
        faild = list(records.values()).count(None)
        success = all - faild

        if tasks is None:
            tasks = all

        result = {
            'tasks':tasks,
            'loss':tasks - all,
            'request':all,
            'success':success,
            'faild':faild
        }

        message = '爬取结果统计信息：\n\t计划总任务数：{tasks} \n\t执行请求总数：{request}，丢失：{loss} \n\t获取成功：{success}，获取失败：{faild}'.format(**result)

        print(message)

        return success



    # async def fetch_all(self,dateList,result):
    #     '''
    #     异步爬虫任务启动处理
    #     :param dateList:
    #     :return:
    #     '''
    #     async with self.sem:
    #         async  with aiohttp.ClientSession() as session:
    #             tasks = []
    #             for index,date in enumerate(dateList):
    #                 if index > 0 and index % self.max_threads == 0:
    #                     await asyncio.sleep(10)
    #                 elif index > 0:
    #                     await asyncio.sleep(1)
    #                 task = asyncio.ensure_future(self.fetch_get(session,date))
    #                 task.add_done_callback(partial(self.fetch_all_callback,date,result))
    #                 tasks.append(task)
    #
    #             await asyncio.wait(tasks)

    # def fetch_all_callback(self,date,result,future):
    #     '''
    #     爬取完成回调处理，合并了任务的爬取结果
    #     :param date:
    #     :param result:
    #     :param future:
    #     :return:
    #     '''
    #     # print("爬取一天记录执行完成，返回结果：(%s)" % date)
    #     records = future.result()
    #     result[date] = records

    def dateRange(self,startAt = None,endAt = None,step=1,format="%Y-%m-%d"):
        '''
        生成日期列表
        :param startAt:
        :param endAt:
        :param step:
        :param format:
        :return:
        '''
        try:
            if startAt is None:
                startAt = self.startAt

            if endAt is None:
                endAt = self.todayDate()

            if isinstance(startAt,(datetime.datetime,datetime.date)) == False:
                startAt = parse(startAt)

            if isinstance(endAt, (datetime.datetime, datetime.date)) == False:
                endAt = parse(endAt)
        except:
            return []

        dateList = rrule.rrule(rrule.DAILY,interval=step,dtstart=startAt,until=endAt)
        return [date.strftime(format) for date in dateList]

    def todayDate(self,toStr = True,format = '%Y-%m-%d'):
        '''
        获取当前数据索引目期
        该网站数据规则为下午dailyStartAt=13:10分开第一期奖至次日零时dailyEndAt=4:05时，但是数据查询日期以第一天为查询
        :return:
        '''

        hm = int(datetime.datetime.now().strftime("%H%M"))

        today = datetime.datetime.now()

        if hm < self.dailyStartAtInt:
            today = today + datetime.timedelta(days=-1)

        if toStr:
            return today.strftime(format)
        else:
            return today

    def isWorking(self,current = None):
        '''
        检查当前时间是否工作时间
        :return:
        '''
        if current is None:
            current = datetime.datetime.now()
        elif isinstance(current, datetime.datetime) == False:
            # 尝试使用其它类型转换为datetime类型
            current = parse(current)

        if isinstance(current, datetime.datetime) == False:
            return False

        currentHM = int(current.strftime("%H%M"))

        if currentHM <= self.dailyEndAtInt or currentHM >= self.dailyStartAtInt:
            return True
        return False
