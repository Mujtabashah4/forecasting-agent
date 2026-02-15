"""
Node 2: Calculate Metrics
Calculates NOV, totals, and budget consumption percentage
"""
from app.agent.state import ForecastAgentState


def calculate_metrics_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Calculate NOV, totals, and percentages.

    Critical Business Rule: NOV = Total POs Issued - Total Actuals
    This represents remaining legal obligation to pay vendors
    """
    forecasts = state['forecasts']
    purchase_orders = state.get('purchase_orders', [])

    # Calculate totals
    state['total_base_forecast'] = sum(f.get('base_forecast', 0) for f in forecasts)
    state['total_forecast_with_rollover'] = sum(f.get('forecast_with_rollover', 0) for f in forecasts)
    state['total_actuals'] = sum(f.get('actual', 0) or 0 for f in forecasts)
    state['total_pos'] = sum(po.get('amount', 0) for po in purchase_orders)

    # Calculate NOV: Total POs - Total Actuals
    # CRITICAL: This is the minimum floor for future forecasts
    state['net_order_value'] = state['total_pos'] - state['total_actuals']

    # Calculate budget consumption
    if state['total_approved'] > 0:
        state['budget_consumption_percent'] = (state['total_actuals'] / state['total_approved']) * 100
    else:
        state['budget_consumption_percent'] = 0

    return state
