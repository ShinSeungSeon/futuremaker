import asyncio
import sys

from futuremaker import log
from futuremaker import utils, indicators
from futuremaker.algo import Algo
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.position_type import Type


class KamaEntry(Algo):
    def __init__(self, base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=10000):
        super().__init__(base=base, quote=quote, floor_decimals=floor_decimals, init_capital=init_capital, max_budget=max_budget)

    def ready(self):
        self.wallet_summary()

    def update_candle(self, df, candle, localtime):

        candle = indicators.kama(df, period=5)
        kama_entry = df['kama']
        roc = df['roc']

        buy_entry = kama_entry[-1] > kama_entry[-2]
        sell_entry = kama_entry[-1] < kama_entry[-2]
        buy_exit = kama_entry[-1] < kama_entry[-2]
        sell_exit = kama_entry[-1] > kama_entry[-2]

        explain = f'{localtime} {candle.close:0.3f}/{kama_entry[-1]:0.3f}:{kama_entry[-2]:0.3f}:{roc[-1]:0.3f}:{roc[-2]:0.3f}'
        if buy_entry:
            # buy_entry
            if self.position_quantity < 0:
                log.logger.info(f'--> Close Short <-- {localtime}')
                quantity = self.close_short()
                self.calc_close(localtime, candle.close, self.position_entry_price, -quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {localtime}')
                self.open_long()
                print(explain)
                self.calc_open(Type.LONG, localtime, candle.close, 0)
        elif buy_exit and self.position_quantity > 0:
            # close long
            log.logger.info(f'--> Exit Long <-- {localtime}')
            quantity = self.close_long()
            self.calc_close(localtime, candle.close, self.position_entry_price, quantity)

        if sell_entry:
            # sell_entry
            if self.position_quantity > 0:
                log.logger.info(f'--> Close Long <-- {localtime}')
                quantity = self.close_long()
                self.calc_close(localtime, candle.close, self.position_entry_price, quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Short <-- {localtime}')
                self.open_short()
                print(explain)
                self.calc_open(Type.SHORT, localtime, candle.close, 0)
        elif sell_exit and self.position_quantity < 0:
            # close sell
            log.logger.info(f'--> Exit Short <-- {localtime}')
            quantity = self.close_short()
            self.calc_close(localtime, candle.close, self.position_entry_price, -quantity)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2020
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=24 * 7 * 2,
                   candle_period='1h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                    test_data='../candle_data/BITFINEX_BTCUSD, 240.csv',
                   )

    algo = KamaEntry(base='BTC', quote='USDT', floor_decimals=3, init_capital=10000, max_budget=1000000)

    asyncio.run(test_bot.run(algo))


