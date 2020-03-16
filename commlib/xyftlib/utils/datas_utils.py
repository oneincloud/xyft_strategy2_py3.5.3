'''
行情数据工具套件
'''
import datetime
import importlib
import os
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from commlib.xyftlib.grabs.grab_base import GrabBase
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

class DatasUtils():

    dayStartTime = "13:10"  # 开始时间
    dayStartStopTime = "13:08"
    dayStartTimeNum = 1310
    dayEndTime = "4:10"  # 结束时间
    dayEndStopTime = "4:03"
    dayEndTimeNum = 410
    dayTotalOptins = 180  # 每天最多期数
    optionInterval = 5  # 每期隔间分钟数
    betLine = 90  # 停止投投时间，秒数



    @classmethod
    def getGrabInstance(cls, grabName=None):
        '''
        获取数据爬虫实例
        :param grap:    指定获取的爬虫实例，不指定时返回所有可用爬虫
        :return:
        '''
        # 可用爬虫
        grabs = ['huangjia', 'zhibo']

        # import爬虫处理器
        grabInstances = {}
        for grab in grabs:
            try:
                className = "Grab{}".format(grab.capitalize())
                moduleName = "grab_{}".format(grab)
                mod = importlib.import_module("commlib.xyftlib.grabs.{}".format(moduleName))

                grabInstances[grab] = getattr(mod, className)()
            except Exception as e:
                print(e)
                pass

        # if grabName is not None and grabName in grabInstances:
        #     print("pppp1")
        #     return grabInstances[grabName]
        # else:
        #     print("pppp2")

        # return grabInstances
        return grabInstances[grabName]

    @classmethod
    def isWorking(cls,current = None):
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

        if currentHM <= cls.dayEndTimeNum or currentHM >= cls.dayStartTimeNum:
            return True
        return False

    @classmethod
    def currentOptionInfo(cls):
        '''
        根据当前时间获取开奖期数信息
        :return:
        '''

        result = {
            'nextOption': 0,  # 当前期数（未开），即下一期
            'nextOpenTime': None,  # 当前期数开奖时间
            'nextStopTime': None,  # 当前期数停止投注时间
            'lastOption': 0,  # 上期期数（已开）
            'lastOpenTime': None,  # 上期期数开奖时间
            'todaySurplus': cls.dayTotalOptins,  # 今天剩余期数
        }

        # now值可以控制后续的运算
        now = datetime.datetime.now()
        # now = parse("2020-02-04 13:10:10")

        timeNum = int(now.strftime("%H%M"))
        dateNum = str(int(now.strftime("%Y%m%d")))

        if timeNum < cls.dayStartTimeNum:  # 在每天开盘时间13:10前，调整日期为前一天
            dateNum = str(int((now + relativedelta(days=-1)).strftime("%Y%m%d")))

        if timeNum > cls.dayEndTimeNum and timeNum < cls.dayStartTimeNum:
            # 非交易时间段
            # print("P1非交易时间段")
            result['lastOption'] = dateNum + "180"
            result["lastOpenTime"] = parse(dateNum + " " + cls.dayEndTime + ":00").strftime(
                "%Y-%m-%d %H:%M:%S")
            result['todaySurplus'] = 0

            result['nextOption'] = now.strftime("%Y%m%d") + "001"
            result['nextOpenTime'] = parse(now.strftime("%Y-%m-%d " + cls.dayStartTime + ":00")).strftime(
                "%Y-%m-%d %H:%M:%S")
            result['nextStopTime'] = parse(
                now.strftime("%Y-%m-%d " + cls.dayStartStopTime + ":00")).strftime("%Y-%m-%d %H:%M:%S")
        else:
            # 交易时间
            # print("P2交易时间")
            timeNum = (timeNum // cls.optionInterval) * cls.optionInterval

            strTimeNum = str(timeNum).zfill(4)

            todayAt = parse(dateNum + " " + cls.dayStartTime + ":00")
            currentAt = parse(now.strftime("%Y%m%d") + " " + ":".join([strTimeNum[:2], strTimeNum[2:], '00']))

            # print("todayAt={}".format(todayAt.strftime("%Y-%m-%d %H:%M:%S")))
            # print("currentAt={}".format(currentAt.strftime("%Y-%m-%d %H:%M:%S")))

            # 计算当前时间期数相关分钟数
            diffMinute = int((currentAt - todayAt).total_seconds() // 60)

            # 当前期数（5分钟一期）
            index = (diffMinute // 5) + 1

            result['lastOption'] = dateNum + str(index).zfill(3)
            result["lastOpenTime"] = currentAt.strftime("%Y-%m-%d %H:%M:%S")
            result["todaySurplus"] = 180 - index

            # print("diffMinute={},index={}".format(diffMinute,index))

            if index >= 180:
                # print("P3")
                nextDay = now + relativedelta(days=+1)
                result['nextOption'] = nextDay.strftime("%Y%m%d") + "001"
                result["nextOpenTime"] = parse(
                    nextDay.strftime("%Y-%m-%d " + cls.dayStartTime + ":00")).strftime("%Y-%m-%d %H:%M:%S")
                result['nextStopTime'] = parse(
                    nextDay.strftime("%Y-%m-%d " + cls.dayStartStopTime + ":00")).strftime(
                    "%Y-%m-%d %H:%M:%S")
            else:
                # print("P4")
                result['nextOption'] = dateNum + str(index + 1).zfill(3)
                result["nextOpenTime"] = (currentAt + relativedelta(minutes=+cls.optionInterval)).strftime(
                    "%Y-%m-%d %H:%M:%S")
                result["nextStopTime"] = (currentAt + relativedelta(
                    seconds=+(cls.optionInterval * 60 - cls.betLine))).strftime(
                    "%Y-%m-%d %H:%M:%S")

        return result

    @classmethod
    def optionDetails(cls,issue):
        '''
        根据开奖期数计算详情
        :param issue:
        :return:
        '''
        issue = int(issue)

        # 分拆日期、索引
        date,index = str(issue)[:8],int(str(issue)[-3:])

        minutes = (index-1) * cls.optionInterval

        openAt = parse(date + ' ' + cls.dayStartTime) + relativedelta(minutes=minutes)
        betStartAt = openAt + relativedelta(minutes=-cls.optionInterval)
        betStopAt = openAt + relativedelta(minutes=-3) # 投注停止时间为开奖前90秒，机器投注提前3分钟
        betStopAt = openAt + relativedelta(seconds=-1)   # 开发，将停止投注时间调整为开奖时间

        # print("openAt",openAt)
        # print("betStartAt",betStartAt)
        # print("betStopAt",betStopAt)

        now = datetime.datetime.now()

        status = -1

        if now < betStartAt:
            status = 0      # 未开始投注
        elif now >= betStartAt and now < betStopAt:
            status = 1      # 可以投注
        elif now >= betStopAt and now < openAt:
            status = 2      # 停止投注
        else:
            status = 3      # 已开奖

        openNums = [0 for i in range(10)]
        if status == 3:
            # TODO:尝试从数据库中读取开奖记录
            pass

        fmt = "%Y-%m-%d %H:%M:%S"

        details = {
            'issue': issue,
            'openAt': openAt.strftime(fmt),  # 开奖时间
            'betStartAt': betStartAt.strftime(fmt),  # 开始投注时间
            'betStopAt': betStopAt.strftime(fmt),  # 停止投注时间
            'status': status,  # 状态码：0未开始投注，1可以投注，2停止投注，3已开奖
            'openNums': openNums  # 已开奖的号码，未开奖时会为0
        }

        return details

    @classmethod
    def todayDate(cls,toStr = True,format = '%Y-%m-%d'):
        '''
        获取当前数据索引目期
        该网站数据规则为下午dailyStartAt=13:10分开第一期奖至次日零时dailyEndAt=4:05时，但是数据查询日期以第一天为查询
        :return:
        '''

        hm = int(datetime.datetime.now().strftime("%H%M"))

        today = datetime.datetime.now()

        if hm < cls.dayStartTimeNum:
            today = today + datetime.timedelta(days=-1)

        if toStr:
            return today.strftime(format)
        else:
            return today

    @classmethod
    def loadDatas(cls,issue=0,days = 5):
        '''
        获取获历史行情数据
        :param issue:       起始期号
        :param days:        历史行情天数
        :return:
        '''
        print("获取获历史行情数据")
        endAt = GrabBase().todayDate()
        if issue > 0:
            # 根据期号获取起始日期
            startAt = parse(str(issue)[:8]).strftime("%Y-%m-%d")
        else:
            # 获取提前指定天数据起始日期
            startAt = parse(endAt) + relativedelta(days=-(days-1))
            startAt = startAt.strftime("%Y-%m-%d")

        # 爬取行情
        instance = cls.getGrabInstance('huangjia')
        records = instance.loadAll(startAt=startAt,endAt=endAt)

        # 将记录转换为DataFrame
        df = instance.toDataFrame(records)

        # 过滤记录集
        df = df[df['issue'] > issue]

        # df.set_index('issue',inplace=True)
        # df.sort_index(ascending=False,inplace=True)

        df.sort_values(by='issue',ascending=False,inplace=True)

        return df

    @classmethod
    def loadDatasByDateList(cls,dateList=None,dateListAndFname=None):
        '''
        根据日期列表爬取数据列表
        :param dateList:        只爬取数据并返回
        :param dateListAndFname  爬取数据并保存文件
        :return:
        '''

        if dateListAndFname is not None and isinstance(dateListAndFname,dict):
            dateList = []
            for date,fname in dateListAndFname.items():
                dateList.append(date)

        if dateList is None or isinstance(dateList,(list,tuple,set)) == False or len(dateList) == 0:
            return None

        # 爬取行情
        instance = cls.getGrabInstance('huangjia')
        records = instance.loadByDateList(dateList=dateList)

        # 将记录转换为DataFrame
        df = instance.toDataFrame(records)
        df.sort_values(by='issue', ascending=False, inplace=True)

        df['date'] = df['open_at'].map(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d'))

        # 以日期分组
        grouped = df.groupby(by="date",sort=True)

        result = {}
        for date,group in grouped:
            del  group['date']
            result[date] = group

        if dateListAndFname is not None and isinstance(dateListAndFname, dict):
            for date,fname in dateListAndFname.items():
                if date in result:
                    fpath,fname = os.path.split(fname)
                    ext = os.path.splitext(fname)[-1][1:]
                    instance.saveTo(records=result[date],fpath=fpath,fname=fname,ext=ext)

        return result

    @classmethod
    def toDataFrame(cls,records):
        '''
        将数据转换为DataFrame
        :param records:
        :return:
        '''
        alllist = []
        if isinstance(records, list):
            alllist = records
        elif isinstance(records, dict):
            for daliy in records.values():
                if isinstance(daliy, list):
                    alllist.extend(daliy)

        columns = ['issue', 'open_at'] + ['r' + str(i + 1) for i in range(10)]
        df = pd.DataFrame(alllist, columns=columns)

        # 设置数据类型
        df['issue'] = df['issue'].astype(np.int64)
        df['open_at'] = df['open_at'].astype(np.datetime64)
        for i in range(1, 11):
            r = 'r' + str(i)
            df[r] = df[r].astype(np.int)

        return df






