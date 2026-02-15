"""
Node 6: Generate Scenarios
Generates forecast scenarios based on analysis
"""
from app.agent.state import ForecastAgentState


def generate_scenarios_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Generate forecast scenarios based on analysis.

    Business Rule: All scenarios must respect NOV as minimum floor
    """
    scenarios = []
    forecasts = state['forecasts']

    # Get future months (no actuals yet)
    future_months = [f for f in forecasts if f.get('actual') is None]

    # Scenario 1: No Change
    scenario1_forecasts = [
        {'month': f['month'], 'amount': f.get('forecast_with_rollover', 0)}
        for f in future_months
    ]
    total1 = sum(f['amount'] for f in scenario1_forecasts) + state['total_actuals']

    scenarios.append({
        'scenario_id': 'scenario-1',
        'name': 'No Change',
        'description': 'Keep current forecasts unchanged',
        'forecasts': scenario1_forecasts,
        'total_year_forecast': total1,
        'variance_from_budget': total1 - state['total_budget']
    })

    # Scenario 2: If large POs exist, spread across months
    large_pos = [p for p in state.get('po_analysis', []) if p.get('needs_review')]
    if large_pos:
        total_large_pos = sum(p['amount'] for p in large_pos)
        months_remaining = len(future_months)
        if months_remaining > 0:
            spread_amount = total_large_pos / months_remaining
            scenario2_forecasts = [
                {'month': f['month'], 'amount': round(spread_amount, 2)}
                for f in future_months
            ]
            total2 = sum(f['amount'] for f in scenario2_forecasts) + state['total_actuals']

            scenarios.append({
                'scenario_id': 'scenario-2',
                'name': 'Spread Large POs',
                'description': f'Spread ${total_large_pos:,.0f} across {months_remaining} months (${spread_amount:,.0f}/month)',
                'forecasts': scenario2_forecasts,
                'total_year_forecast': total2,
                'variance_from_budget': total2 - state['total_budget'],
                'suggested_reason_codes': [
                    {'code': 'normal_variance', 'suggested_percent': 100}
                ]
            })

    # Scenario 3: Adjust for variance trend
    if state['variances']:
        total_variance = sum(v['variance'] for v in state['variances'])
        if total_variance > 0:
            months_remaining = len(future_months)
            if months_remaining > 0:
                adjustment = total_variance / months_remaining
                scenario3_forecasts = [
                    {'month': f['month'], 'amount': f.get('forecast_with_rollover', 0) + adjustment}
                    for f in future_months
                ]
                total3 = sum(f['amount'] for f in scenario3_forecasts) + state['total_actuals']

                scenarios.append({
                    'scenario_id': 'scenario-3',
                    'name': 'Adjust for Variance Trend',
                    'description': f'Increase remaining months by ${adjustment:,.0f} each to cover observed variance',
                    'forecasts': scenario3_forecasts,
                    'total_year_forecast': total3,
                    'variance_from_budget': total3 - state['total_budget'],
                    'suggested_reason_codes': [
                        {'code': 'inflation', 'suggested_percent': 60},
                        {'code': 'normal_variance', 'suggested_percent': 40}
                    ]
                })

    state['scenarios'] = scenarios
    return state
