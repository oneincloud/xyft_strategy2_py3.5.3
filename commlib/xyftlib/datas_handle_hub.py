import datetime
import pandas as pd
from PyQt5.Qt import *
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


class DatasUpdateHistoryThread(QThread):
    '''
    更新历史数据
    '''

    updated = pyqtSignal(object)

    def __init__(self, mainWin):
        super().__init__()
        self.mainWin = mainWin
        self.session = mainWin.session
        self.serverAddr = mainWin.serverAddr
        self.history = mainWin.history

    def run(self):

        if self.serverAddr is None or self.session is None:
            return None

        url = self.serverAddr + '/datas/history'

        _from = 0

        if self.history is not None:
            _from = self.history[0].max()

        res = self.session.get(url, data={'from': _from})

        if res.status_code == 200:
            rJson = res.json()

            if len(rJson['history']) > 0:
                result_df = pd.DataFrame(rJson['history'])
                result_df.sort_values(by=0, ascending=False, inplace=True)

                if self.mainWin.history is None:
                    self.mainWin.history = result_df.copy()
                else:
                    self.mainWin.history = self.mainWin.history.append(result_df, ignore_index=True)

                # 更新上一期开奖号码显示
                if self.mainWin.currentOptionInfo is not None and self.mainWin.history is not None:
                    lastOption = int(self.mainWin.currentOptionInfo['lastOption'])
                    # print("lastOption=%d" % lastOption)
                    # print(self.mainWin.history)
                    record = self.mainWin.history[self.mainWin.history[0] == lastOption]

                    if len(record) > 0:
                        for i in range(10):
                            self.mainWin.txtNx[i].setText(str(record.iloc[0][i+2]))
                    else:
                        for i in range(10):
                            self.mainWin.txtNx[i].setText('?')

                # 历史数据更新成功通知信号
                #self.updated.emit(result_df.copy())

# 数据相关处理类
class DatasHandleHub():
    '''
    数据相关处理类
    '''
    dayStartTime = "13:10"      # 开始时间
    dayStartStopTime = "13:08"
    dayStartTimeNum = 1310
    dayEndTime = "4:05"         # 结束时间
    dayEndStopTime = "4:03"
    dayEndTimeNum = 405
    dayTotalOptins = 180        # 每天最多期数
    optionInterval = 5          # 每期隔间分钟数
    betLine = 90               # 停止投投时间，秒数

    @staticmethod
    def showOptionInfo(mainWin):
        '''
        显示期数数据
        :return:
        '''
        currentOptionInfo = DatasHandleHub.currentOptionInfo()

        # 期数
        mainWin.txtNextOption.setText(str(currentOptionInfo['nextOption']))
        mainWin.txtLastOption.setText(str(currentOptionInfo['lastOption']))
        mainWin.txtTodaySurplus.setText(str(currentOptionInfo['todaySurplus']))

        # 时间倒计时
        mainWin.txtNextOpenTime.setText(DatasHandleHub.countDown(currentOptionInfo['nextOpenTime']))
        mainWin.txtNextStopTime.setText(DatasHandleHub.countDown(currentOptionInfo['nextStopTime']))

        mainWin.currentOptionInfo = currentOptionInfo


    @staticmethod
    def countDown(target,now = None):
        '''
        显示倒计时
        :param target:
        :param now:
        :return:
        '''
        if now is None:
            now = datetime.datetime.now()
        else:
            now = parse(now)

        target = parse(target)

        total_seconds = int((target-now).total_seconds())

        _s = 0
        _m = 0
        _h = 0

        if total_seconds > 0:
            # 时：分：秒 计时器
            _s = total_seconds % 60
            _m = (total_seconds // 60) % 60
            _h = (total_seconds // 3600) % 24

        _s = str(_s).zfill(2)
        _m = str(_m).zfill(2)
        _h = str(_h).zfill(2)

        return ":".join([_h,_m,_s])


    @staticmethod
    def currentOptionInfo(now = None):
        '''
        根据当前时间获取开奖期数信息
        :return:
        '''

        result = {
            'nextOption':0,         # 当前期数（未开），即下一期
            'nextOpenTime':None,    # 当前期数开奖时间
            'nextStopTime':None,    # 当前期数停止投注时间
            'lastOption':0,         # 上期期数（已开）
            'lastOpenTime':None,        # 上期期数开奖时间
            'todaySurplus':DatasHandleHub.dayTotalOptins,     # 今天剩余期数
        }


        now = datetime.datetime.now()
        # now = parse("2020-02-04 13:10:10")

        timeNum = int(now.strftime("%H%M"))
        dateNum = str(int(now.strftime("%Y%m%d")))

        if timeNum < DatasHandleHub.dayStartTimeNum:  # 在每天开盘时间13:10前，调整日期为前一天
            dateNum = str(int((now + relativedelta(days=-1)).strftime("%Y%m%d")))

        if timeNum > DatasHandleHub.dayEndTimeNum and timeNum < DatasHandleHub.dayStartTimeNum:
            # 非交易时间段
            # print("P1非交易时间段")
            result['lastOption'] = dateNum + "180"
            result["lastOpenTime"] = parse(dateNum + " " + DatasHandleHub.dayEndTime + ":00").strftime("%Y-%m-%d %H:%M:%S")
            result['todaySurplus'] = 0

            result['nextOption'] = now.strftime("%Y%m%d") + "001"
            result['nextOpenTime'] = parse(now.strftime("%Y-%m-%d " + DatasHandleHub.dayStartTime + ":00")).strftime("%Y-%m-%d %H:%M:%S")
            result['nextStopTime'] = parse(now.strftime("%Y-%m-%d " + DatasHandleHub.dayStartStopTime + ":00")).strftime("%Y-%m-%d %H:%M:%S")
        else:
            # 交易时间
            # print("P2交易时间")
            timeNum = (timeNum // DatasHandleHub.optionInterval) * DatasHandleHub.optionInterval

            strTimeNum = str(timeNum).zfill(4)

            todayAt = parse(dateNum + " " + DatasHandleHub.dayStartTime + ":00")
            currentAt = parse(now.strftime("%Y%m%d") + " " + ":".join([strTimeNum[:2],strTimeNum[2:],'00']))

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
                result["nextOpenTime"] = parse(nextDay.strftime("%Y-%m-%d "+DatasHandleHub.dayStartTime+":00")).strftime("%Y-%m-%d %H:%M:%S")
                result['nextStopTime'] = parse(nextDay.strftime("%Y-%m-%d " + DatasHandleHub.dayStartStopTime + ":00")).strftime("%Y-%m-%d %H:%M:%S")
            else:
                # print("P4")
                result['nextOption'] = dateNum + str(index+1).zfill(3)
                result["nextOpenTime"] = (currentAt + relativedelta(minutes=+DatasHandleHub.optionInterval)).strftime("%Y-%m-%d %H:%M:%S")
                result["nextStopTime"] = (currentAt + relativedelta(seconds=+(DatasHandleHub.optionInterval*60 - DatasHandleHub.betLine))).strftime("%Y-%m-%d %H:%M:%S")

        return result

    @staticmethod
    def updatedHistoryCallback(mainWin, hitory):
        '''
        历史数据加载完成
        :param mainWin:
        :param hitory:
        :return:
        '''
        print("历史数据加载完成=>updatedHistoryCallback()")

