'''
直播网
https://www.cp9345.com/
'''
import datetime
from commlib.xyftlib.grabs.grab_base import GrabBase

class GrabZhibo(GrabBase):

    def __init__(self):
        '''
        直播网构造器
        '''
        print('[-------------------直播网构造器-------------------]')
        self.website = '直播网'
        self.domain = 'https://www.cp9345.com/'
        self.startAt = datetime.date(2019,2,3)

        # super().__init__(startAt=self.startAt,domain=self.domain)
        GrabBase.__init__(self)

    async def initSession(self):
        '''
        网站自定义初始化请求会话方法
        :return:
        '''
        print("网站自定义初始化请求会话方法")


    def fetch(self,date):
        '''
        爬取数据实现方法
        :param date:
        :return:
        '''


