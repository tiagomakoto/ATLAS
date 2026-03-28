from core.event_bus import emit_event
from core.analytics_engine import *

def publish_analytics(prices, ir_series):
    returns = compute_returns(prices)

    emit_event(compute_walk_forward(ir_series))
    emit_event(compute_distribution(returns))
    emit_event(compute_acf(returns))
    emit_event(compute_tail_metrics(returns))