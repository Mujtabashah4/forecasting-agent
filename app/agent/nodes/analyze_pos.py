"""
Node 5: Analyze Purchase Orders
Analyzes POs for large orders that need review
"""
from app.agent.state import ForecastAgentState


def analyze_pos_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Analyze purchase orders for large POs that need review.

    Business Rule: Flag PO if amount > 2x average monthly forecast
    """
    purchase_orders = state.get('purchase_orders', [])
    po_analysis = []

    # Calculate average monthly forecast
    avg_monthly = state['total_base_forecast'] / 12 if state['total_base_forecast'] > 0 else 0

    for po in purchase_orders:
        po_amount = po.get('amount', 0)

        # Flag if PO is more than 2x average monthly forecast
        if avg_monthly > 0 and po_amount > (avg_monthly * 2):
            ratio = po_amount / avg_monthly
            po_analysis.append({
                'po_number': po.get('po_number'),
                'amount': po_amount,
                'monthly_avg': avg_monthly,
                'ratio': round(ratio, 1),
                'issue_date': po.get('issue_date'),
                'status': po.get('status'),
                'needs_review': True
            })

            # Add to flags
            state['flags'].append({
                'type': 'large_po',
                'severity': 'high',
                'po_number': po.get('po_number'),
                'po_amount': po_amount,
                'monthly_forecast': avg_monthly,
                'ratio': round(ratio, 1),
                'message': f"PO {po.get('po_number')} (${po_amount:,.0f}) is {ratio:.1f}x larger than average monthly forecast (${avg_monthly:,.0f})"
            })

    state['po_analysis'] = po_analysis
    return state
