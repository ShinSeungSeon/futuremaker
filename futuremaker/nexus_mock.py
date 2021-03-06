import sys
import traceback
from datetime import datetime

import pandas as pd

from futuremaker import utils, data_ingest
from futuremaker.log import logger
import os


class Nexus(object):

    def __init__(self, candle_limit, test_start=None, test_end=None, test_data=None):
        self.candle_handler = None
        self.cb_update_candle = None
        self.candle_limit = candle_limit
        self.test_start = datetime.strptime(test_start, '%Y-%m-%d') if test_start else None
        self.test_end = datetime.strptime(test_end, '%Y-%m-%d') if test_end else None
        self.test_data = test_data

    def callback(self, update_candle=None, **kwargs):
        """
        데이터 변경시 호출되는 콜백함수들을 설정한다.
        """
        self.cb_update_candle = update_candle

    def _update_candle(self):
        candle_df = self.candle_handler.update()

        # 캔들업뎃호출
        if self.cb_update_candle and candle_df is not None:
            if self.test_start is not None and candle_df.index[-1] < self.test_start:
                # skip
                return 0

            if self.test_end is not None and candle_df.index[-1] > self.test_end:
                # skip
                return 0
            try:
                self.cb_update_candle(candle_df, candle_df.iloc[-1])
                return candle_df
            except Exception as e:
                try:
                    exc_info = sys.exc_info()
                finally:
                    self.send_message(e)
                    traceback.print_exception(*exc_info)
                    del exc_info

    async def start(self):
        if not self.candle_handler:
            logger.error('Nexus mock is not loaded yet!')
            return

        logger.info('Backtest start timer!')
        while True:
            df = self._update_candle()
            if df is None:
                break

    async def load(self):
        try:
            self.candle_handler = FileCandleHandler(self.test_data, self.candle_limit)
            self.candle_handler.load()
        except:
            utils.print_traceback()


class FileCandleHandler(object):

    def __init__(self, filepath, history):
        self.filepath = filepath
        self.history = history
        self._data = None
        self._seq = 0
        self._size = 0

    @staticmethod
    def date_parse(time_in_secs):
        return datetime.fromtimestamp(float(time_in_secs))

    def load(self):
        logger.info(f'Load data: {os.path.abspath(self.filepath)}')
        self._data = pd.read_csv(self.filepath, index_col='time',
                                 usecols=['time', 'open', 'high', 'low', 'close', 'volume'],
                                 parse_dates=['time'],
                                 date_parser=lambda epoch: pd.to_datetime(epoch, unit='s')
                                 )
        self._size = len(self._data.index)

    def update(self):
        if self._seq + self.history <= self._size:
            # copy() 를 사용하지 않으면 SettingWithCopyWarning 가 발생하므로 꼭 사용.
            df = self._data.iloc[self._seq:self._seq + self.history].copy()
            self._seq += 1
            return df
