import asyncio
import sys

from futuremaker import log
from futuremaker import utils, indicators
from futuremaker.algo import Algo
from futuremaker.binance_api import BinanceAPI
from futuremaker.bot import Bot
from futuremaker.position_type import Type


class RocEntry(Algo):
    def __init__(self, base, quote, floor_decimals, init_capital, max_budget,
                 period, paper, buy_unit, buy_delay, commission_rate=0.1):
        super().__init__(base=base, quote=quote, floor_decimals=floor_decimals, init_capital=init_capital,
                         max_budget=max_budget, commission_rate=commission_rate, paper=paper,
                         buy_unit=buy_unit, buy_delay=buy_delay)
        self.period = period

    def ready(self):
        self.wallet_summary()

    def update_candle(self, df, candle, localtime):
        candle = indicators.roc(df, period=self.period)
        roc = df['roc']

        buy_entry = roc[-2] < 0 and roc[-1] > 0
        sell_entry = roc[-2] < 0 and roc[-1] < 0
        buy_exit = (roc[-2] > 0 and roc[-1] < 0)
        sell_exit = (roc[-2] < 0 and roc[-1] > 0)

        explain = f'{localtime} close[{candle.close:0.3f}] roc[{roc[-2]:0.1f}, {roc[-1]:0.1f}] entry_time[{self.position_entry_time}]'

        if not self.backtest:
            log.logger.info(explain)
            self.send_message(explain)

        if buy_entry:
            # buy_entry
            if self.position_quantity < 0:
                log.logger.info(f'--> Close Short <-- {localtime}')
                quantity = self.close_short()
                self.calc_close(localtime, candle.close, self.position_entry_price, -quantity)
            if self.position_quantity == 0:
                log.logger.info(f'--> Enter Long <-- {localtime}')
                self.open_long()
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
                self.calc_open(Type.SHORT, localtime, candle.close, 0)
        elif sell_exit and self.position_quantity < 0:
            # close sell
            log.logger.info(f'--> Exit Short <-- {localtime}')
            quantity = self.close_short()
            self.calc_close(localtime, candle.close, self.position_entry_price, -quantity)


if __name__ == '__main__':
    params = utils.parse_param_map(sys.argv[1:])
    year = 2019
    test_bot = Bot(None, symbol='BTCUSDT', candle_limit=10,
                   candle_period='4h',
                   test_start=f'{year}-01-01', test_end=f'{year}-12-31',
                   # test_data='../candle_data/BINANCE_BNBUSDT, 1D.csv',
                   # test_data='../candle_data/BITFINEX_BTCUSD, 240.csv',
                   # test_data='../candle_data/BINANCE_BNBUSDT, 240.csv',
                   # test_data='../candle_data/BINANCE_ETHUSDT, 240.csv',
                   test_data='../candle_data/BITFINEX_BABUSD, 240.csv',
                   # test_data='../candle_data/BINANCE_BTCUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_ETHUSDT, 240.csv'
                   # test_data='../candle_data/BINANCE_BTCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_BTCUSD, 120.csv'
                   # test_data='../candle_data/BINANCE_ETCUSDT, 60.csv'
                   # test_data='../candle_data/BITFINEX_ETHUSD, 60.csv'
                   )
    real_bot = Bot(BinanceAPI(), symbol='BTCUSDT', candle_limit=10,
                   backtest=False, candle_period='1m')

    algo = RocEntry(base='BTC', quote='USDT', period=5, paper=True, floor_decimals=2,
                    init_capital=1000, max_budget=1000000, buy_unit=0.01, buy_delay=1)

    # asyncio.run(test_bot.run(algo))
    asyncio.run(real_bot.run(algo))

"""
# BTCUSD
2015: TOT_EQUITY:4213 TOT_PROFIT:3213 (321.35%) DD:4.2% MDD:16.7% TOT_TRADE:338 WIN%:37.0% P/L:3.4
2016: TOT_EQUITY:3987 TOT_PROFIT:2987 (298.67%) DD:4.9% MDD:14.5% TOT_TRADE:384 WIN%:42.7% P/L:2.6
2017: TOT_EQUITY:17423 TOT_PROFIT:16423 (1642.31%) DD:0.1% MDD:21.5% TOT_TRADE:333 WIN%:46.5% P/L:2.3
2018: TOT_EQUITY:2930 TOT_PROFIT:1930 (193.02%) DD:18.3% MDD:30.8% TOT_TRADE:371 WIN%:39.6% P/L:1.9
2019: TOT_EQUITY:4069 TOT_PROFIT:3069 (306.93%) DD:2.1% MDD:16.2% TOT_TRADE:403 WIN%:35.5% P/L:2.7
# BNBUSDT
2019: TOT_EQUITY:3319 TOT_PROFIT:2319 (231.95%) DD:0.0% MDD:31.5% TOT_TRADE:377 WIN%:38.7% P/L:2.0
2018: TOT_EQUITY:19400 TOT_PROFIT:18400 (1839.99%) DD:4.0% MDD:45.1% TOT_TRADE:381 WIN%:38.8% P/L:2.2
# ETHUSDT
2018: TOT_EQUITY:9928 TOT_PROFIT:8928 (892.83%) DD:13.9% MDD:34.4% TOT_TRADE:356 WIN%:41.6% P/L:1.9
2019: TOT_EQUITY:2295 TOT_PROFIT:1295 (129.51%) DD:10.3% MDD:27.2% TOT_TRADE:408 WIN%:35.3% P/L:2.2
# BSVUSD
2019 TOT_EQUITY:2525 TOT_PROFIT:1525 (152.53%) DD:7.0% MDD:60.8% TOT_TRADE:428 WIN%:32.2% P/L:2.8
# BABUSD
2019 TOT_EQUITY:2079 TOT_PROFIT:1079 (107.87%) DD:25.4% MDD:58.7% TOT_TRADE:412 WIN%:31.6% P/L:2.5
"""