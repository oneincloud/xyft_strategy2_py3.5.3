from PyQt5.QtWidgets import QMainWindow,QMessageBox,QTableWidgetItem
from PyQt5.Qt import QThread,pyqtSignal,QTimer,QBrush,QColor
from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import Qt
from client.resource.ui.Strategy2MainWindow_UI import Ui_MainWindow
import datetime
from dateutil.parser import parse
import copy
import pandas as pd

from commlib.xyftlib.utils.datas_utils import DatasUtils
from commlib.xyftlib.datas_handle_hub import DatasHandleHub
from commlib.xyftlib.pandas_model import PandasModel

class MyPandasModel(PandasModel):


    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(),index.column()])
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignVCenter | Qt.AlignCenter
            return None

class DatasUpdateThread(QThread):
    '''
    使用多线程更新行情UI
    '''
    updated = pyqtSignal(object)

    def __init__(self):
        super().__init__()

    def run(self):
        datas = DatasUtils.loadDatas(days=1)

        if datas is not None and isinstance(datas,pd.DataFrame) and len(datas) > 0:
            self.updated.emit(datas)

# 主窗体类
class Strategy2MainWindow(QMainWindow,Ui_MainWindow):

    def __init__(self):
        super(Strategy2MainWindow,self).__init__()
        self.setupUi(self)

        self.prevAt = 161  # default:161
        self.prevLimit = 9  # default:9

        self.txtPrevAt.setText(str(self.prevAt))
        self.txtPrevLimit.setText(str(self.prevLimit))

        self.txtNx = [self.txtN1, self.txtN2, self.txtN3, self.txtN4, self.txtN5, self.txtN6, self.txtN7, self.txtN8,
                      self.txtN9, self.txtN10]

        self.currentOptionInfo = None  # 当前期数信息
        self.currentOptionIssue = 0  # 当前最新期号

        self.__initSounds()
        self.__initBusiness()

    def __initBusiness(self):
        '''
        初始化业务处理
        :return:
        '''
        # UI界面的一些初始化
        self.tableTodayRecords.horizontalHeader().setStyleSheet('QHeaderView::section{background:#f0f0f0}')
        self.tableTodayRecords.setColumnWidth(0,120)

        self.tableTips.horizontalHeader().setStyleSheet('QHeaderView::section{background:#f0f0f0}')
        self.tableTips.verticalHeader().setStyleSheet('QHeaderView::section{background:#f0f0f0}')
        self.showOptionInfo()
        self.updateTableViewToday(None)

        # # 历史数据
        self.datasUpdateThread = DatasUpdateThread()
        self.datasUpdateThread.updated.connect(self.datasTopUpdateShow)
        self.datasUpdateThread.updated.connect(self.datasUpdatedCall)
        self.datasUpdateThread.updated.connect(self.updateTableViewToday)
        self.datasUpdateThread.start()

        # 全局定时器
        self.gIntervalTimer = QTimer()
        self.gIntervalTimer.timeout.connect(self.gIntervalTimerCall)
        self.gIntervalTimer.start(1000)     # 启动定时器

        self.currentCounter = []        # 当计分析计数器

    def __initSounds(self):
        '''
        加载提示音效
        :return:
        '''
        # self.soundLightMusic = QSound(r'client\resource\sounds\00_ligth_music.wav',self)  # 轻音乐
        # self.soundWin = QSound(r'client\resource\sounds\01_win.wav',self)  # 中奖提示
        # self.soundLoss = QSound(r'client\resource\sounds\01_loss.wav',self) # 全输提示
        # self.soundAooo = QSound(r'client\resource\sounds\02_aooo.wav', self)  # 断网提示
        # self.soundNewMessage = QSound(r'client\resource\sounds\03_new_message.wav', self)  # 提注提示
        # self.soundIOSShort = QSound(r'client\resource\sounds\04_ios_short.wav', self)  # 提注提示
        #
        # self.soundZhoJi = QSound(r'client\resource\sounds\06_qibinghao_shengli.wav', self)  # 开始召集
        #
        # # self.soundZhoJi.setLoops(5)
        # # self.soundZhoJi.play()
        #
        # # self.soundLightMusic.play()
        # # self.soundWin.play()
        # # self.soundAooo.play()
        # # self.soundNewMessage.play()
        # # self.soundIOSShort.play()

        # 提示音相关状态位
        self.tipsCounter = 0        # 当预测目标有变化时发出提示音
        self.winIssue = 0           # 中奖提示音，防止行情更新重复播放
        self.trigger = 2           # 当达到触发条件是，最多播入提示声次数

        self.currentTestIssue = 0   # 当前测算期数

    def showOptionInfo(self):
        '''
        显示期数数据
        :return:
        '''
        currentOptionInfo = DatasHandleHub.currentOptionInfo()

        # 期数
        self.txtNextOption.setText(str(currentOptionInfo['nextOption']))
        # self.txtLastOption.setText(str(currentOptionInfo['lastOption']))
        self.txtTodaySurplus.setText(str(currentOptionInfo['todaySurplus']))

        # 时间倒计时
        self.txtNextOpenTime.setText(self.countDown(currentOptionInfo['nextOpenTime']))
        self.txtNextStopTime.setText(self.countDown(currentOptionInfo['nextStopTime']))

        self.currentOptionInfo = currentOptionInfo

    def countDown(self,target,now = None):
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

    def gIntervalTimerCall(self):
        '''
        全局定时器刷新
        :param mainWin:
        :return:
        '''
        # print("全局定时器刷新：{}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        # 刷新期数、开奖结果、倒计时
        self.showOptionInfo()

        # 第隔3秒更新行情（开奖）记录数据
        now = datetime.datetime.now()

        now_minute = int(now.strftime("%M"))
        now_second = int(now.strftime("%S"))

        # if now_minute % 5 == 0 and now_second in [1,5,10]:
        #     self.datasUpdateProcess.start()

        self.datasUpdateThread.start()

    def datasTopUpdateShow(self,datas):
        '''
        更新显示当前最新结果
        :param records:
        :return:
        '''
        # print("更新显示当前最新结果")
        # print(datas)

        df = datas.sort_values(by='issue', ascending=False)

        newLastOptionIssue = df.iloc[0][0]

        if newLastOptionIssue > self.currentOptionIssue:
            self.currentOptionIssue = newLastOptionIssue

            # TODO： 新的开奖记录 ，发开提示声音
            print("TODO： 新的开奖记录 ，发开提示声音")
            # self.soundIOSShort.play()

            # 更新开奖记录显示
            self.txtLastOption.setText(str(newLastOptionIssue))

            for i in range(10):
                col = "r" + str(i + 1)
                self.txtNx[i].setText(str(df.iloc[0][i + 2]))
                #self.txtNx[i].setPixmap(self.pixNum[df.iloc[0][i + 2]])

    def datasUpdatedCall(self,datas):
        '''
        根据行情分析提示结果
        :param datas:
        :return:
        '''
        if datas is None or len(datas) == 0:
            # self.soundAooo.play()
            return

        # 根据行情分析提示结果
        print("根据行情分析提示结果")

        # 过滤当前记录
        df = pd.DataFrame(datas)
        currentDate = DatasUtils.todayDate()
        df['date'] = df['open_at'].map(lambda x:datetime.datetime.strftime(x,'%Y-%m-%d'))
        df = df[df['date'] == currentDate]
        df.sort_values(by="issue",ascending=True,inplace=True)

        issue = df['issue'].max()

        index = int(str(issue)[-3:])

        # 统计
        subDf = df.copy()
        if len(subDf) > self.prevAt:
            subDf = subDf.iloc[0:self.prevAt]

        counter = []
        for r in range(1, 11):
            col = "r" + str(r)
            grouped = subDf.groupby(by=col)
            for num, group in grouped:
                if len(group) <= self.prevLimit:

                    count = len(group)

                    # 计算目标是否确认？
                    status = "待确认"
                    if self.prevAt - index < self.prevLimit:
                        if count + self.prevAt - index <= self.prevLimit:
                            status = "已确认"

                    counter.append({
                        "r": r,
                        "n": num,
                        "count": count,
                        'status':status  # True 已确认，False 待确认
                    })

        self.currentCounter = copy.deepcopy(counter)

        tips = ""

        if index < self.prevAt:
            # 未达到目标遇测
            tips = "距离：%d 期，预测目标：%d" % (self.prevAt - index,len(counter))

            # 统计有变动即提示
            if len(counter) != self.tipsCounter:
                # 提示变动
                # self.soundNewMessage.play()
                pass

            # 记录新的计数
            self.tipsCounter = len(counter)

            self.updateTableViewTips(counter)
        elif index == self.prevAt:
            if len(counter) > 0:
                tips = "触发：%d期，符合结果：共 %d 目标" % (self.prevAt,len(counter))
                if self.trigger > 0:
                    # # self.soundWin.play()
                    # self.soundZhoJi.setLoops(3)
                    # self.soundZhoJi.play()
                    pass
            else:
                tips = "触发：%d期，符合结果：0 目标" % self.prevAt
                if self.trigger > 0:
                    # self.soundAooo.play()
                    pass

            self.trigger -= 1
            self.updateTableViewTips(counter)
        else:
            tips = "触发：%d期，符合结果：共 %d 目标" % (self.prevAt, len(counter))


        # 计算中奖记录，变形counter
        if index > self.prevAt and self.currentTestIssue < df['issue'].max():

            self.currentTestIssue = df['issue'].max()

            # 提取已开奖记录
            tops = df.iloc[self.prevAt:]
            # tops = pd.DataFrame(tops)

            # print(tops)

            # 构造记录分板
            bets = []
            lastRoundHasWin = False
            for topIndex,row in tops.iterrows():
                # print(row)
                lastRoundHasWin = False

                issueIndex = int(str(row['issue'])[-3:])
                for cc in counter:
                    col = "r" + str(cc['r'])

                    # print(col)
                    bet = {
                        'groupK': "x".join([str(v) for v in [cc['r'],cc['n'],cc['count']]]),
                        'index':issueIndex,
                        'issue':row['issue'],
                        'open_at':row['open_at'],
                        'r':cc['r'],
                        'n':cc['n'],
                        'count':cc['count'],
                        'open':row[col],
                        'win':"胜" if row[col] == cc['n'] else "负"
                    }

                    if row[col] == cc['n']:
                        lastRoundHasWin = True

                    bets.append(bet)

            bets = pd.DataFrame(bets)
            # print(bets)

            haftA = (180 - self.prevAt) // 2
            haftB = haftA
            if haftA * 2 < (180 - self.prevAt):
                haftA += 1

            newCounter = []
            grouped = bets.groupby(by="groupK")
            for groupK,group in grouped:
                r,n,c = tuple(str(groupK).split("x"))

                haftBGroup = group.iloc[haftB:]

                row = {
                    'r':r,
                    'n':n,
                    'count':c,
                    'allWin':len(group[group['win'] == '胜']),
                    'allLoss':len(group[group['win'] == '负']),
                    'haftBWin':len(haftBGroup[haftBGroup['win'] == '胜']),
                    'haftBLoss': len(haftBGroup[haftBGroup['win'] == '负']),
                }
                newCounter.append(row)

            # 更新TableViews
            self.updateTableViewTips(newCounter)

            if lastRoundHasWin:
                # 本轮有赢
                # self.soundWin.play()
                pass
            else:
                # 本轮全输
                # self.soundLoss.play()
                pass
        if tips != "":
            self.txtTips.setText(tips)

        if index != len(df):
            # 期数引索与开奖记录数不一到致，开奖期数可能不完整
            QMessageBox.critical(self,"警告","注意！注意！注意！开奖期数可能不完整！")


    def updateTableViewToday(self,datas):
        '''
        更新今天开奖记录显示
        :param datas:
        :return:
        '''
        columns = ['issue','open_at','r1','r2','r3','r4','r5','r6','r7','r8','r9','r10']

        df = None

        if datas is not None and len(datas) > 0:
            df = pd.DataFrame(datas)
            del datas['date']

            df['open_at'] = df['open_at'].map(lambda x: datetime.datetime.strftime(x, '%Y-%m-%d %H:%M'))
        else:
            df = pd.DataFrame(columns=columns)

        df.rename(columns={
            'issue':'期号',
            'open_at':'开奖时间',
            'r1':'1道',
            'r2':'2道',
            'r3':'3道',
            'r4':'4道',
            'r5':'5道',
            'r6':'6道',
            'r7':'7道',
            'r8':'8道',
            'r9':'9道',
            'r10':'10道'
        },inplace=True)

        model = MyPandasModel(df)
        self.tableTodayRecords.setModel(model)

        self.tableTodayRecords.setColumnWidth(0, 120)
        self.tableTodayRecords.setColumnWidth(1, 160)


    def updateTableViewTips(self,records):
        '''
        更新提示统计记录列表
        :param records:
        :return:
        '''

        columns = ['r', 'n', 'count', 'status']

        df = None

        self.tableTips.setRowCount(0)

        if records is not None and len(records) > 0:

            df = pd.DataFrame(records)
            df.sort_values(by="count", ascending=True, inplace=True)
            self.tableTips.setRowCount(len(df))

            # 检查是否带有已开奖记录
            if len(records[0]) > 4:

                self.tableTips.setColumnHidden(3,True)
                self.tableTips.setColumnHidden(4,False)
                self.tableTips.setColumnHidden(5, False)
                self.tableTips.setColumnHidden(6, False)
                self.tableTips.setColumnHidden(7, False)


                rowIndex = 0
                for index, row in df.iterrows():
                    # print(row)
                    itemR = QTableWidgetItem(str(row['r']))
                    itemR.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 0, itemR)

                    itemN = QTableWidgetItem(str(row['n']))
                    itemN.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 1, itemN)

                    itemC = QTableWidgetItem(str(row['count']))
                    itemC.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 2, itemC)

                    itemAllWin = QTableWidgetItem(str(row['allWin']))
                    itemAllWin.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 4, itemAllWin)

                    itemAllLoss = QTableWidgetItem(str(row['allLoss']))
                    itemAllLoss.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 5, itemAllLoss)

                    itemHaftBWin = QTableWidgetItem(str(row['haftBWin']))
                    itemHaftBWin.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 6, itemHaftBWin)

                    itemHaftBLoss = QTableWidgetItem(str(row['haftBLoss']))
                    itemHaftBLoss.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 7, itemHaftBLoss)


                    rowIndex += 1
            else:

                self.tableTips.setColumnHidden(3, False)
                self.tableTips.setColumnHidden(4, True)
                self.tableTips.setColumnHidden(5, True)
                self.tableTips.setColumnHidden(6, True)
                self.tableTips.setColumnHidden(7, True)

                rowIndex = 0
                for index,row in df.iterrows():
                    # print(row)
                    itemR = QTableWidgetItem(str(row['r']))
                    itemR.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 0, itemR)

                    itemN = QTableWidgetItem(str(row['n']))
                    itemN.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 1, itemN)

                    itemC = QTableWidgetItem(str(row['count']))
                    itemC.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.tableTips.setItem(rowIndex, 2, itemC)

                    itemS = QTableWidgetItem(row['status'])

                    if row['status'] != "已确认":
                        itemS.setForeground(QBrush(QColor(255,0,0)))

                    itemS.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.tableTips.setItem(rowIndex, 3, itemS)

                    rowIndex += 1
        else:
            self.tableTips.setColumnHidden(3, False)
            self.tableTips.setColumnHidden(4, True)
            self.tableTips.setColumnHidden(5, True)
            self.tableTips.setColumnHidden(6, True)
            self.tableTips.setColumnHidden(7, True)
            df = pd.DataFrame(columns=columns)
            self.tableTips.setRowCount(0)


    def closeEvent(self, QCloseEvent):
        '''
        退出程序窗口事件
        :param QCloseEvent:
        :return:
        '''
        #  使用QMessageBox提示
        reply = QMessageBox.warning(self, "温馨提示", "即将退出, 确定？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if (reply == QMessageBox.Yes):
            QCloseEvent.accept()
        if (reply == QMessageBox.No):
            QCloseEvent.ignore()

