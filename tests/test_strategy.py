from trading.strategy_ema import EMAStrategy


def test_ema_crossover_signal():
    strategy = EMAStrategy(fast_period=2, slow_period=3)
    prices = [1, 1, 1, 2, 3]
    signals = strategy.generate_signals("BTCUSDT", prices)
    assert signals
    assert signals[0].side == "BUY"
