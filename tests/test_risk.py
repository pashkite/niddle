from trading.risk import RiskLimits, RiskManager


def test_risk_blocks_after_losses():
    limits = RiskLimits(daily_loss_limit_pct=0.1, max_consecutive_losses=2, cooldown_minutes=30)
    risk = RiskManager(limits, initial_equity=1000)

    risk.record_trade_pnl(-10)
    allowed, _ = risk.can_trade()
    assert allowed

    risk.record_trade_pnl(-20)
    allowed, reason = risk.can_trade()
    assert not allowed
    assert "consecutive" in reason.lower()
