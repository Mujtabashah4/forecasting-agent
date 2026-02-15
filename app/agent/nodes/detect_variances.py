"""
Node 3: Detect Variances
Finds months where actuals exceed forecast
"""
from app.agent.state import ForecastAgentState


def detect_variances_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Find months where actuals exceed forecast.

    Business Rule: Flag if variance > 5%
    """
    forecasts = state['forecasts']
    variances = []
    flags = []

    for f in forecasts:
        actual = f.get('actual')
        if actual is None:
            continue  # No actual yet

        forecast = f.get('forecast_with_rollover', f.get('base_forecast', 0))
        variance = actual - forecast

        if forecast > 0:
            variance_percent = (variance / forecast) * 100
        else:
            variance_percent = 0

        variances.append({
            'month': f['month'],
            'forecast': forecast,
            'actual': actual,
            'variance': variance,
            'variance_percent': round(variance_percent, 2)
        })

        # Flag if variance exceeds 5%
        if variance_percent > 5:
            severity = 'high' if variance_percent > 15 else 'medium'
            flags.append({
                'type': 'variance_exceeded',
                'severity': severity,
                'month': f['month'],
                'forecast': forecast,
                'actual': actual,
                'variance': variance,
                'variance_percent': round(variance_percent, 2),
                'message': f"Month {f['month']} actuals (${actual:,.0f}) exceeded forecast (${forecast:,.0f}) by {abs(variance_percent):.1f}%"
            })

    state['variances'] = variances
    state['flags'] = flags
    return state
