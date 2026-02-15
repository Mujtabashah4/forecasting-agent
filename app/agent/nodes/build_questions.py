"""
Node 7: Build Questions
Builds questions for user based on detected flags
"""
from app.agent.state import ForecastAgentState


def build_questions_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Build questions for user based on flags.

    Business Rule: Ask human for guidance on large POs, variances, thresholds
    """
    questions = []
    question_id = 1

    # Question for large POs
    large_po_flags = [f for f in state['flags'] if f['type'] == 'large_po']
    if large_po_flags:
        for flag in large_po_flags:
            questions.append({
                'question_id': f'q{question_id}',
                'type': 'large_po_review',
                'priority': 'high',
                'related_flag': flag,
                'text': f"A large PO ({flag['po_number']}) of ${flag['po_amount']:,.0f} was issued, significantly exceeding the monthly forecast. How should this be handled?",
                'options': [
                    {'value': 'spread', 'label': 'Spread over multiple months', 'follow_up': 'How many months?'},
                    {'value': 'increase', 'label': 'Increase forecast to match'},
                    {'value': 'no_action', 'label': 'No action needed (already accounted for)'}
                ],
                'requires_reason': True
            })
            question_id += 1

    # Question for variances
    variance_flags = [f for f in state['flags'] if f['type'] == 'variance_exceeded']
    if variance_flags:
        questions.append({
            'question_id': f'q{question_id}',
            'type': 'variance_review',
            'priority': 'medium',
            'text': f"Actuals exceeded forecasts in {len(variance_flags)} month(s). Would you like to adjust the forecast for remaining months?",
            'options': [
                {'value': 'yes', 'label': 'Yes, increase remaining months'},
                {'value': 'no', 'label': 'No, keep current forecast'},
                {'value': 'custom', 'label': 'Specify custom adjustment'}
            ],
            'requires_reason': True
        })
        question_id += 1

    # Question for threshold alerts
    if state['threshold_alerts']:
        for alert in state['threshold_alerts']:
            if alert['type'] == 'budget_threshold':
                questions.append({
                    'question_id': f'q{question_id}',
                    'type': 'threshold_alert',
                    'priority': 'high',
                    'text': f"Budget consumption has reached {alert['current']}%, exceeding the 90% threshold. How would you like to proceed?",
                    'options': [
                        {'value': 'acknowledge', 'label': 'Acknowledge and continue'},
                        {'value': 'review', 'label': 'Flag for management review'},
                        {'value': 'request_increase', 'label': 'Request budget increase'}
                    ],
                    'requires_reason': False
                })
                question_id += 1

    state['questions'] = questions
    return state
