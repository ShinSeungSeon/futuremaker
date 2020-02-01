import asyncio
import concurrent
import os
import threading
import time
from datetime import datetime

import requests
from aiohttp import web
from collections import deque

from futuremaker import utils
from futuremaker.nexus import Nexus
from futuremaker import nexus_mock
from futuremaker.log import logger


class Bot(object):
    """
    봇.
    nexus 객체를 가지고 있으며 다음과 같이 사용가능하다.
    nexus.api: 오더, 잔고, 히스토리 api 호출
    nexus['<토픽'>]: 웹소켓으로 업데이트되는 토픽데이터가 담기는 저장소. 값이 필요할때 접근가능하다.
    """

    def __init__(self, api, symbol, candle_limit=20, candle_period='1h', since=None, dry_run=True,
                 backtest=True, test_start=None, test_end=None, test_data=None,
                 telegram_bot_token=None, telegram_chat_id=None):

        if not symbol:
            raise Exception('Symbol must be set.')
        if not candle_period:
            raise Exception('candle_period must be set. 1m, 5m,..')

        self.messages = deque()
        self.api = api
        self.symbol = symbol
        self.candle_period = candle_period
        self.backtest = backtest
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

        if not self.backtest:
            self.nexus = Nexus(api, symbol, candle_limit=candle_limit, candle_period=candle_period, dry_run=dry_run)
        else:
            self.nexus = nexus_mock.Nexus(candle_limit, test_start, test_end, test_data)

    def start_sched(self):
        loop = asyncio.new_event_loop()
        # print('Thread Event Loop > ', loop)
        loop.run_until_complete(self.sched())

    async def sched(self):
        while True:
            try:
                while self.messages:
                    item = self.messages.popleft()
                    await self.__send_telegram(item)
                    await asyncio.sleep(0.5)
                else:
                    await asyncio.sleep(1)
            except:
                utils.print_traceback()

    def send_message(self, text):
        if not self.backtest:
            self.messages.append(text)
        else:
            print('BotToken 과 ChatId 가 설정되어 있지 않아 텔레그램 메시지를 보내지 않습니다.')

    async def __send_telegram(self, text):
        if self.telegram_bot_token and self.telegram_chat_id:
            return await utils.send_telegram(self.telegram_bot_token, self.telegram_chat_id, text)

    async def run(self, algo):
        self.nexus.callback(update_orderbook=algo.update_orderbook,
                            update_candle=algo.update_candle,
                            update_order=algo.update_order,
                            update_position=algo.update_position)

        algo.api = self.api
        algo.send_message = self.send_message

        try:
            logger.info('SYMBOL: %s', self.symbol)
            logger.info('CANDLE_PERIOD: %s', self.candle_period)
            logger.info('NOW: %s', datetime.now())
            logger.info('UCT: %s', datetime.utcnow())
            logger.info('ENV[TZ]: %s', os.getenv("TZ"))
            logger.info('LOGLEVEL: %s', os.getenv("LOGLEVEL"))
            logger.info('TZNAME: %s', time.tzname)
            ip_address = requests.get('https://api.ipify.org?format=json').json()['ip']
            logger.info('IP: %s', ip_address)
            self.send_message(f'{algo.get_name()} Bot started.. {ip_address}')
            logger.info('Loading...')

            t = threading.Thread(target=self.start_sched,  daemon=True)
            t.start()
            await self.nexus.load()
            logger.info('Start!')
            await self.nexus.start()
        except KeyboardInterrupt:
            pass
