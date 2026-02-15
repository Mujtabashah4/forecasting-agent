"""
Node: Check Project Status
Detects if project is late and checks PO delivery dates against forecasts

Client Requirements:
1. If the project is LATE, ask human if there's a risk the project will cost more
2. If anticipated delivery of equipment > forecast for next month, flag for review
"""
from app.agent.state import ForecastAgentState
from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def check_project_status_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Check project status for delays and PO delivery issues.

    Business Rules:
    1. Project is LATE if current date > anticipated_end_date and status != 'complete'
    2. Flag each PO where estimated_delivery month > current month forecast
    3. Ask human about potential cost overruns for late projects
    """
    project = state['project']
    current_month = state['current_month']

    # Check 1: Is the project late?
    project_late_flag = _check_project_late(project, state)
    if project_late_flag:
        state['flags'].append(project_late_flag)
        # Add question for human about cost risk
        state['questions'].append({
            'question_id': f"q_late_{project.get('id', 'unknown')}",
            'type': 'project_late_review',
            'priority': 'high',
            'text': f"Project '{project.get('name', 'Unknown')}' appears to be past its anticipated end date ({project.get('anticipated_end_date')}). Is there a risk that the project will cost more than forecast?",
            'options': [
                {'value': 'yes_increase', 'label': 'Yes, likely to cost more', 'follow_up': 'By how much?'},
                {'value': 'yes_minor', 'label': 'Yes, but minor increase expected'},
                {'value': 'no_on_track', 'label': 'No, project is on track despite date'},
                {'value': 'pending_review', 'label': 'Need more information to assess'}
            ],
            'requires_reason': True
        })

    # Check 2: PO delivery dates vs monthly forecasts
    po_delivery_flags = _check_po_delivery_dates(state, current_month)
    for flag in po_delivery_flags:
        state['flags'].append(flag)
        # Add question for each flagged PO
        state['questions'].append({
            'question_id': f"q_delivery_{flag.get('po_number', 'unknown')}",
            'type': 'po_delivery_review',
            'priority': 'medium',
            'text': f"PO {flag.get('po_number')} (${flag.get('po_amount'):,.0f}) has estimated delivery in month {flag.get('delivery_month')}, but the forecast for that month is only ${flag.get('monthly_forecast'):,.0f}. How should this be handled?",
            'options': [
                {'value': 'increase_forecast', 'label': 'Increase forecast to match PO'},
                {'value': 'spread_months', 'label': 'Spread delivery across months'},
                {'value': 'delay_expected', 'label': 'Delivery will likely be delayed'},
                {'value': 'already_accounted', 'label': 'Already accounted for in forecast'}
            ],
            'requires_reason': True
        })

    return state


def _check_project_late(project: dict, state: ForecastAgentState) -> Optional[dict]:
    """
    Check if project is past its anticipated end date.

    A project is considered LATE if:
    1. Current date > anticipated_end_date
    2. Project status is not 'complete' or 'closed'
    """
    anticipated_end = project.get('anticipated_end_date')
    status = project.get('status', '').lower()

    if not anticipated_end:
        return None

    # Skip if project is already complete
    if status in ['complete', 'completed', 'closed']:
        return None

    try:
        # Parse the anticipated end date
        if isinstance(anticipated_end, str):
            end_date = datetime.strptime(anticipated_end, '%Y-%m-%d').date()
        elif isinstance(anticipated_end, (datetime, date)):
            end_date = anticipated_end if isinstance(anticipated_end, date) else anticipated_end.date()
        else:
            return None

        today = date.today()

        if today > end_date:
            days_late = (today - end_date).days

            # Determine severity based on how late
            if days_late > 90:
                severity = 'critical'
            elif days_late > 30:
                severity = 'high'
            else:
                severity = 'medium'

            logger.warning(
                f"Project {project.get('id')} is {days_late} days past anticipated end date"
            )

            return {
                'type': 'project_late',
                'severity': severity,
                'project_id': project.get('id'),
                'project_name': project.get('name'),
                'anticipated_end_date': str(end_date),
                'days_late': days_late,
                'message': f"Project is {days_late} days past anticipated end date ({end_date}). Review for potential cost overruns."
            }

    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse anticipated_end_date: {anticipated_end} - {e}")

    return None


def _check_po_delivery_dates(state: ForecastAgentState, current_month: int) -> list:
    """
    Check if any PO's estimated delivery exceeds the forecast for that month.

    Client Requirement:
    "If the anticipated delivery of equipment is higher than the forecast
    for the next month, flag each project (ask human review)"
    """
    flags = []
    purchase_orders = state.get('purchase_orders', [])
    forecasts = state.get('forecasts', [])

    # Build a lookup of forecasts by month
    forecast_by_month = {
        f['month']: f.get('forecast_with_rollover', f.get('base_forecast', 0))
        for f in forecasts
    }

    for po in purchase_orders:
        estimated_delivery = po.get('estimated_delivery')
        po_amount = po.get('amount', 0)
        po_status = po.get('status', '').lower()

        # Skip if already delivered or cancelled
        if po_status in ['delivered', 'cancelled', 'closed']:
            continue

        if not estimated_delivery:
            continue

        try:
            # Parse delivery date
            if isinstance(estimated_delivery, str):
                delivery_date = datetime.strptime(estimated_delivery, '%Y-%m-%d')
            else:
                delivery_date = estimated_delivery

            delivery_month = delivery_date.month

            # Only check future months
            if delivery_month < current_month:
                continue

            # Get forecast for delivery month
            monthly_forecast = forecast_by_month.get(delivery_month, 0)

            # Flag if PO amount > monthly forecast
            if po_amount > monthly_forecast and monthly_forecast > 0:
                excess_ratio = po_amount / monthly_forecast

                # Only flag significant excesses (> 1.5x)
                if excess_ratio > 1.5:
                    severity = 'high' if excess_ratio > 3 else 'medium'

                    flags.append({
                        'type': 'po_delivery_exceeds_forecast',
                        'severity': severity,
                        'po_number': po.get('po_number'),
                        'po_amount': po_amount,
                        'delivery_month': delivery_month,
                        'estimated_delivery': str(delivery_date.date()),
                        'monthly_forecast': monthly_forecast,
                        'excess_ratio': round(excess_ratio, 1),
                        'message': f"PO {po.get('po_number')} delivery (${po_amount:,.0f}) in month {delivery_month} exceeds forecast (${monthly_forecast:,.0f}) by {excess_ratio:.1f}x"
                    })

                    logger.info(
                        f"PO {po.get('po_number')} flagged: delivery ${po_amount:,.0f} > forecast ${monthly_forecast:,.0f}"
                    )

        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse PO delivery date: {estimated_delivery} - {e}")

    return flags
