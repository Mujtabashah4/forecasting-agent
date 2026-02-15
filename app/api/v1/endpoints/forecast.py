"""
Forecast review endpoint
Main endpoint for forecast analysis
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.request import ForecastReviewRequest
from app.schemas.response import ForecastReviewResponse
from app.schemas.common import Analysis
from app.api.deps import get_current_user
from app.agent.workflow import run_forecast_analysis
from app.services.session_storage import session_storage
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/forecast/review", response_model=ForecastReviewResponse)
async def review_forecast(
    request: ForecastReviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze project forecast and generate recommendations.

    This is the main endpoint that Capexplan calls to get forecast analysis.

    Business Rules:
    - Reviews FUTURE months only (current + onwards)
    - Never modifies past actuals
    - Respects NOV as minimum floor
    - Returns recommendations to TEMP TABLE
    - Human-in-the-loop (no auto-apply)

    Args:
        request: Forecast review request with project data

    Returns:
        ForecastReviewResponse: Analysis results with scenarios and questions
    """
    try:
        logger.info(f"Processing forecast review request: {request.request_id}")
        logger.info(f"Project: {request.project.name} (ID: {request.project.id})")

        # Run workflow asynchronously
        result = await run_forecast_analysis(request.model_dump())

        # Build response from result state
        response = ForecastReviewResponse(
            request_id=result['request_id'],
            session_id=result['session_id'],
            status=result['status'].value,
            analysis=Analysis(
                summary=result['summary'],
                budget=result['total_budget'],
                approved_amount=result['total_approved'],
                total_base_forecast=result['total_base_forecast'],
                total_forecast_with_rollover=result['total_forecast_with_rollover'],
                total_actuals_to_date=result['total_actuals'],
                budget_consumption_percent=result['budget_consumption_percent'],
                net_order_value=result['net_order_value'],
                months_with_actuals=result['months_with_actuals'],
                months_remaining=result['months_remaining']
            ),
            flags=result['flags'],
            threshold_alerts=result['threshold_alerts'],
            questions=result['questions'],
            scenarios=result['scenarios'],
            explanation=result['explanation'],
            timestamp=result['timestamp']
        )

        logger.info(f"Successfully completed forecast review: {request.request_id}")
        logger.info(f"Generated {len(result['scenarios'])} scenarios, {len(result['flags'])} flags")

        # Store session for later reference (scenario approval, responses)
        session_storage.store_session(
            session_id=result['session_id'],
            data={
                'request_id': result['request_id'],
                'project': request.project.model_dump(),
                'scenarios': result['scenarios'],
                'flags': result['flags'],
                'questions': result['questions'],
                'threshold_alerts': result['threshold_alerts'],
                'analysis': response.analysis.model_dump(),
                'timestamp': result['timestamp']
            }
        )

        # Store original forecast in history
        session_storage.store_forecast_history(
            project_id=request.project.id,
            forecasts=[f.model_dump() for f in request.forecasts],
            revision_type='original'
        )

        logger.info(f"Session {result['session_id']} stored for later reference")

        return response

    except Exception as e:
        logger.error(f"Error processing forecast review: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing forecast review: {str(e)}"
        )
