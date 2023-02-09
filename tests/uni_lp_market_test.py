import unittest
from decimal import Decimal

import demeter
from demeter import UniLpMarket, TokenInfo, UniV3Pool, UniV3PoolStatus, Broker, MarketInfo

test_market = MarketInfo("market1")


class TestUniLpMarket(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.eth = TokenInfo(name="eth", decimal=18)
        self.usdc = TokenInfo(name="usdc", decimal=6)
        self.pool = UniV3Pool(self.usdc, self.eth, 0.05, self.usdc)
        super(TestUniLpMarket, self).__init__(*args, **kwargs)

    def test_price(self):
        broker = self.get_broker()
        print(broker.markets[test_market].tick_to_price(206600))
        self.assertEqual(broker.markets[test_market].tick_to_price(206600).quantize(Decimal("1.00000")),
                         Decimal("1066.41096"))

    def get_broker(self):
        broker = Broker()
        market = UniLpMarket(self.pool)
        broker.add_market(test_market, market)
        tick = 200000
        price = market.tick_to_price(tick)
        market.market_status = UniV3PoolStatus(None, tick, Decimal("840860039126296093"),
                                               Decimal("18714189922"), Decimal("58280013108171131649"), price)
        broker.set_asset(self.eth, 1)
        broker.set_asset(self.usdc, price)
        market.sqrt_price = demeter.broker.uni_lp_helper.tick_to_sqrtPriceX96(tick)
        return broker

    def check_type(self, broker):
        self.assertTrue(type(broker.assets[self.usdc].balance) is Decimal)
        self.assertTrue(type(broker.assets[self.usdc].decimal) is int)

    @staticmethod
    def print_broker(broker, positions=[]):
        if positions:
            for p in positions:
                print("=====begin print position=====")
                print(p)
                print(broker.positions[p])
                print("=====end======")
        print("broker:", broker)

    def test_new(self):
        broker = self.get_broker()
        print(broker)
        uni_market: UniLpMarket = broker.markets[test_market]
        self.assertEqual(uni_market.market_status.price, broker.assets[self.usdc].balance)
        self.assertEqual(1, broker.assets[self.eth].balance)
        self.assertEqual(uni_market.token0, self.usdc)
        self.assertEqual(uni_market.token1, self.eth)
        self.check_type(broker)

    # TODO continue from here !
    def test_add_Liquidity(self):
        broker = self.get_broker()
        (new_position, base_used, quote_used, liquidity) = broker.add_liquidity(broker.pool_status.price - 100,
                                                                                broker.pool_status.price + 100,
                                                                                broker.asset0.balance,
                                                                                broker.asset1.balance)
        TestUniLpMarket.print_broker(broker, [new_position, ])

    def test_add_Liquidity_by_tick(self):
        broker = self.get_broker()
        # should use all the balance
        (new_position, base_used, quote_used, liquidity) = \
            broker._add_liquidity_by_tick(broker.pool_status.price / 2,
                                          Decimal(0.5),
                                          broker.pool_status.current_tick - 100,
                                          broker.pool_status.current_tick + 100)
        TestUniLpMarket.print_broker(broker, [new_position, ])
        self.assertEqual(0.5, round(broker.asset1.balance, 4))

    def test_add_Liquidity_by_tick_again(self):
        broker = self.get_broker()
        # should use all the balance
        (new_position1, base_used1, quote_used1, liquidity1) = \
            broker._add_liquidity_by_tick(broker.pool_status.price / 2,
                                          Decimal(0.5),
                                          broker.pool_status.current_tick - 100,
                                          broker.pool_status.current_tick + 100)
        TestUniLpMarket.print_broker(broker, [new_position1, ])
        self.assertEqual(0.5, round(broker.asset1.balance, 4))
        (new_position2, base_used2, quote_used2, liquidity2) = \
            broker._add_liquidity_by_tick(broker.pool_status.price / 2,
                                          Decimal(0.5),
                                          broker.pool_status.current_tick - 100,
                                          broker.pool_status.current_tick + 100)
        TestUniLpMarket.print_broker(broker, [new_position2, ])
        self.assertEqual(base_used1, base_used2)
        self.assertEqual(quote_used1, quote_used2)
        self.assertEqual(liquidity1, liquidity2)
        self.assertEqual(new_position1, new_position2)
        self.assertEqual(liquidity1 + liquidity2, broker.positions[new_position1].liquidity)

    def test_add_Liquidity_use_all_balance(self):
        broker = self.get_broker()
        # should use all the balance
        (new_position, base_used, quote_used, liquidity) = broker._add_liquidity_by_tick(broker.pool_status.price,
                                                                                         Decimal(1),
                                                                                         broker.pool_status.current_tick - 1000,
                                                                                         broker.pool_status.current_tick + 1000,
                                                                                         broker.sqrt_price)
        print(new_position, base_used, quote_used, liquidity)
        TestUniLpMarket.print_broker(broker, [new_position, ])
        self.assertEqual(0, broker.asset0.balance.quantize(Decimal('.000001')))
        self.assertEqual(0, broker.asset1.balance.quantize(Decimal('.0000001')))

    def test_remove_position(self):
        broker = self.get_broker()
        token0_amt = broker.asset0.balance
        token1_amt = broker.asset1.balance
        (new_position, base_used, quote_used, liquidity) = broker.add_liquidity_by_tick(
            broker.pool_status.current_tick - 100,
            broker.pool_status.current_tick + 100,
            token0_amt,
            token1_amt)
        TestUniLpMarket.print_broker(broker, [new_position, ])
        broker.remove_liquidity(new_position)
        print("===============================================================================")
        TestUniLpMarket.print_broker(broker)
        self.assertEqual(token0_amt.quantize(Decimal('.000001')), broker.asset0.balance.quantize(Decimal('.000001')))
        self.assertEqual(token1_amt.quantize(Decimal('.000001')), broker.asset1.balance.quantize(Decimal('.000001')))
        self.assertEqual(len(broker.positions), 0)

    def test_collect_fee(self):
        broker = self.get_broker()
        # should use all the balance
        (new_position, base_used, quote_used, liquidity) = broker._add_liquidity_by_tick(broker.pool_status.price,
                                                                                         Decimal(1),
                                                                                         broker.pool_status.current_tick - 10,
                                                                                         broker.pool_status.current_tick + 10)
        TestUniLpMarket.print_broker(broker, [new_position])
        eth_amount = Decimal("10000000000000000000")
        usdc_amount = Decimal("10000000")
        broker.pool_status = UniV3PoolStatus(None, broker.pool_status.current_tick,
                                             liquidity * 100,
                                             usdc_amount,
                                             eth_amount,
                                             broker.tick_to_price(broker.pool_status.current_tick))
        print("=========after a bar======================================================================")
        broker.update()
        TestUniLpMarket.print_broker(broker, [new_position])
        self.assertTrue(Decimal("0.00005") == broker.position(new_position).pending_amount0)
        self.assertTrue(Decimal("0.00005") == broker.position(new_position).pending_amount1)
        fee0 = broker.position(new_position).pending_amount0
        fee1 = broker.position(new_position).pending_amount1
        balance0 = broker.asset0.balance
        balance1 = broker.asset1.balance
        broker.collect_fee(new_position)
        print("=========collect======================================================================")
        TestUniLpMarket.print_broker(broker, [new_position])
        self.assertEqual(fee0 + balance0, broker.asset0.balance)
        self.assertEqual(fee1 + balance1, broker.asset1.balance)
        self.assertEqual(broker.position(new_position).pending_amount0, 0)
        self.assertEqual(broker.position(new_position).pending_amount0, 0)

    def test_buy(self):
        broker = self.get_broker()
        token0_before = broker.asset0.balance
        token1_before = broker.asset1.balance
        TestUniLpMarket.print_broker(broker)
        broker.buy(0.5)
        print("=========after buy======================================================================")
        TestUniLpMarket.print_broker(broker)
        self.assertEqual(broker.asset0.balance,
                         token0_before - broker.pool_status.price * Decimal(0.5) * (1 + broker.pool_info.fee_rate))
        self.assertEqual(broker.asset1.balance, token1_before + Decimal(0.5))

    def test_sell(self):
        broker = self.get_broker()
        TestUniLpMarket.print_broker(broker)
        token0_before = broker.asset0.balance
        token1_before = broker.asset1.balance
        broker.sell(1)
        print("=========after buy======================================================================")
        TestUniLpMarket.print_broker(broker)
        self.assertEqual(broker.asset0.balance,
                         token0_before + broker.pool_status.price * Decimal(1) * (1 - broker.pool_info.fee_rate))
        self.assertEqual(broker.asset1.balance, token1_before - Decimal(1))

    def test_net_value(self):
        pool0p3 = UniV3Pool(self.usdc, self.eth, 0.3, self.usdc)
        broker = UniLpMarket(pool0p3)
        broker.set_asset(self.usdc, 2000)
        broker.set_asset(self.eth, 1)
        price = 1100
        tick = broker.price_to_tick(price)
        old_net_value = price * broker.asset1.balance + broker.asset0.balance
        pos = broker.add_liquidity_by_tick(broker.price_to_tick(1200), broker.price_to_tick(1000), tick=tick)
        status = broker.get_account_status(Decimal(1100))
        print(pos)
        print(status)
        self.assertEqual(old_net_value, round(status.pool_net_value, 4))

    def test_net_value2(self):
        pool0p3 = UniV3Pool(self.usdc, self.eth, 0.3, self.usdc)
        broker = UniLpMarket(pool0p3)
        broker.set_asset(self.usdc, 1100)
        broker.set_asset(self.eth, 1)
        price = 1100
        old_net_value = price * broker.asset1.balance + broker.asset0.balance
        print(old_net_value)
        tick = broker.price_to_tick(price)
        broker.pool_status = UniV3PoolStatus(None, tick, Decimal(0), Decimal(0), Decimal(0), Decimal(0))
        pos = broker.add_liquidity(1000, 1200)
        status = broker.get_account_status(Decimal(1100))
        print(pos)
        print(status)
        self.assertEqual(old_net_value, round(status.pool_net_value, 4))
