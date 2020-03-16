from PyQt5.QtCore import QAbstractTableModel,Qt
import pandas as pd

class PandasModel(QAbstractTableModel):

    def __init__(self,df_data):
        QAbstractTableModel.__init__(self)
        self._data = df_data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.iloc[index.row(),index.column()])
            return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._data.columns[col]
        return None

class PandaHelper():

    @staticmethod
    def toDataFrame(source_list):
        '''
        将列表字典数据转换为DataFrame
        :return:
        '''
        data = None

        for row in source_list:
            if data is None:
                data = {key:[] for key in row.keys()}

            for key in row:
                data[key].append(row[key])

        if data is None:
            return None
        return pd.DataFrame(data)