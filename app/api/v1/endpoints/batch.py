"""
Batch Processing Endpoints
Analyze multiple projects at once

Client Requirement:
Support batch analysis of multiple projects for monthly review cycles.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.schemas.request import ForecastReviewRequest
from app.schemas.response import ForecastReviewResponse
from app.api.deps import get_current_user
from app.agent.workflow import run_forecast_analysis
from app.services.session_storage import session_storage
from app.utils.helpers import get_current_timestamp
import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()


class BatchReviewRequest(BaseModel):
    """Request for batch forecast review of multiple projects"""
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    projects: List[ForecastReviewRequest] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of project forecast review requests (max 50)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch-2024-04",
                "projects": [
                    {
                        "request_id": "project-1",
                        "project": {
                            "id": "PRJ-001",
                            "code": "PROJ1",
                            "name": "Project 1",
                            "budget": 100000,
                            "approved_amount": 100000,
                            "start_date": "2024-01-01",
                            "anticipated_end_date": "2024-12-31",
                            "status": "active"
                        },
                        "fiscal_year": 2024,
                        "current_month": 4,
                        "forecasts": []
                    }
                ]
            }
        }


class BatchResultSummary(BaseModel):
    """Summary of a single project analysis in batch"""
    request_id: str
    project_id: str
    project_name: str
    status: str
    flags_count: int
    scenarios_count: int
    questions_count: int
    budget_consumption_percent: float
    net_order_value: float
    needs_attention: bool
    error: Optional[str] = None


class BatchReviewResponse(BaseModel):
    """Response for batch forecast review"""
    batch_id: str
    status: str
    total_projects: int
    completed: int
    failed: int
    results: List[BatchResultSummary]
    high_priority_projects: List[str] = Field(
        default_factory=list,
        description="Project IDs that need immediate attention"
    )
    summary: Dict[str, Any]
    timestamp: str


class BatchStatus(BaseModel):
    """Status of a running batch job"""
    batch_id: str
    status: str
    total_projects: int
    completed: int
    failed: int
    in_progress: int
    started_at: str
    estimated_completion: Optional[str] = None


# In-memory batch job storage
batch_jobs: Dict[str, Dict[str, Any]] = {}


@router.post("/review", response_model=BatchReviewResponse)
async def batch_review_forecasts(
    request: BatchReviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze multiple projects in a single request.

    This endpoint allows monthly batch review of all projects at once.
    Useful for end-of-month forecast review cycles.

    Features:
    - Process up to 50 projects in one request
    - Returns summary of all projects
    - Identifies high-priority projects needing attention
    - Provides aggregate statistics
    """
    try:
        logger.info(f"Starting batch review: {request.batch_id} with {len(request.projects)} projects")

        results: List[BatchResultSummary] = []
        completed = 0
        failed = 0
        high_priority_projects = []

        # Aggregate stats
        total_flags = 0
        total_budget = 0
        total_actuals = 0
        projects_over_90_percent = 0
        projects_with_late_flags = 0

        # Process each project
        for project_request in request.projects:
            try:
                # Run analysis
                result = await run_forecast_analysis(project_request.model_dump())

                # Determine if project needs attention
                high_severity_flags = [
                    f for f in result.get('flags', [])
                    if f.get('severity') in ['high', 'critical']
                ]
                has_threshold_alerts = len(result.get('threshold_alerts', [])) > 0
                needs_attention = len(high_severity_flags) > 0 or has_threshold_alerts

                if needs_attention:
                    high_priority_projects.append(project_request.project.id)

                # Build summary
                summary = BatchResultSummary(
                    request_id=project_request.request_id,
                    project_id=project_request.project.id,
                    project_name=project_request.project.name,
                    status=result['status'].value if hasattr(result['status'], 'value') else str(result['status']),
                    flags_count=len(result.get('flags', [])),
                    scenarios_count=len(result.get('scenarios', [])),
                    questions_count=len(result.get('questions', [])),
                    budget_consumption_percent=result.get('budget_consumption_percent', 0),
                    net_order_value=result.get('net_order_value', 0),
                    needs_attention=needs_attention
                )
                results.append(summary)
                completed += 1

                # Update aggregates
                total_flags += len(result.get('flags', []))
                total_budget += result.get('total_budget', 0)
                total_actuals += result.get('total_actuals', 0)
                if result.get('budget_consumption_percent', 0) >= 90:
                    projects_over_90_percent += 1
                if any(f.get('type') == 'project_late' for f in result.get('flags', [])):
                    projects_with_late_flags += 1

                # Store session for later reference
                session_storage.store_session(
                    session_id=result['session_id'],
                    data={
                        'batch_id': request.batch_id,
                        'request_id': result['request_id'],
                        'project': project_request.project.model_dump(),
                        'scenarios': result['scenarios'],
                        'flags': result['flags'],
                        'questions': result['questions'],
                        'timestamp': result['timestamp']
                    }
                )

            except Exception as e:
                logger.error(f"Error processing project {project_request.project.id}: {e}")
                results.append(BatchResultSummary(
                    request_id=project_request.request_id,
                    project_id=project_request.project.id,
                    project_name=project_request.project.name,
                    status="error",
                    flags_count=0,
                    scenarios_count=0,
                    questions_count=0,
                    budget_consumption_percent=0,
                    net_order_value=0,
                    needs_attention=True,
                    error=str(e)
                ))
                failed += 1
                high_priority_projects.append(project_request.project.id)

        # Build aggregate summary
        overall_consumption = (total_actuals / total_budget * 100) if total_budget > 0 else 0
        summary = {
            'total_projects': len(request.projects),
            'projects_needing_attention': len(high_priority_projects),
            'projects_over_90_percent_budget': projects_over_90_percent,
            'projects_with_late_flags': projects_with_late_flags,
            'total_flags_raised': total_flags,
            'average_flags_per_project': round(total_flags / len(request.projects), 1) if request.projects else 0,
            'aggregate_budget': total_budget,
            'aggregate_actuals': total_actuals,
            'aggregate_consumption_percent': round(overall_consumption, 2)
        }

        logger.info(f"Batch {request.batch_id} completed: {completed} success, {failed} failed")

        return BatchReviewResponse(
            batch_id=request.batch_id,
            status="completed" if failed == 0 else "completed_with_errors",
            total_projects=len(request.projects),
            completed=completed,
            failed=failed,
            results=results,
            high_priority_projects=high_priority_projects,
            summary=summary,
            timestamp=get_current_timestamp()
        )

    except Exception as e:
        logger.error(f"Batch review failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch review failed: {str(e)}"
        )


@router.post("/review/async")
async def batch_review_async(
    request: BatchReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Start an async batch review that runs in the background.

    Use this for large batches that may take longer to process.
    Check status with GET /batch/status/{batch_id}
    """
    # Initialize job
    batch_jobs[request.batch_id] = {
        'status': 'pending',
        'total_projects': len(request.projects),
        'completed': 0,
        'failed': 0,
        'started_at': get_current_timestamp(),
        'results': []
    }

    # Add background task
    background_tasks.add_task(
        _process_batch_async,
        request.batch_id,
        request.projects
    )

    return {
        'batch_id': request.batch_id,
        'status': 'started',
        'message': f'Batch job started with {len(request.projects)} projects',
        'check_status_url': f'/api/v1/batch/status/{request.batch_id}'
    }


async def _process_batch_async(batch_id: str, projects: List[ForecastReviewRequest]):
    """Background task to process batch"""
    job = batch_jobs[batch_id]
    job['status'] = 'processing'

    for project in projects:
        try:
            result = await run_forecast_analysis(project.model_dump())
            job['completed'] += 1
            job['results'].append({
                'project_id': project.project.id,
                'status': 'completed',
                'session_id': result['session_id']
            })
        except Exception as e:
            job['failed'] += 1
            job['results'].append({
                'project_id': project.project.id,
                'status': 'error',
                'error': str(e)
            })

    job['status'] = 'completed'
    job['completed_at'] = get_current_timestamp()


@router.get("/status/{batch_id}", response_model=BatchStatus)
async def get_batch_status(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of an async batch job"""
    if batch_id not in batch_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {batch_id} not found"
        )

    job = batch_jobs[batch_id]
    in_progress = job['total_projects'] - job['completed'] - job['failed']

    return BatchStatus(
        batch_id=batch_id,
        status=job['status'],
        total_projects=job['total_projects'],
        completed=job['completed'],
        failed=job['failed'],
        in_progress=in_progress,
        started_at=job['started_at'],
        estimated_completion=job.get('completed_at')
    )


@router.get("/results/{batch_id}")
async def get_batch_results(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get results of a completed async batch job"""
    if batch_id not in batch_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {batch_id} not found"
        )

    job = batch_jobs[batch_id]

    if job['status'] != 'completed':
        return {
            'batch_id': batch_id,
            'status': job['status'],
            'message': 'Batch job is still processing'
        }

    return {
        'batch_id': batch_id,
        'status': 'completed',
        'total_projects': job['total_projects'],
        'completed': job['completed'],
        'failed': job['failed'],
        'results': job['results'],
        'started_at': job['started_at'],
        'completed_at': job.get('completed_at')
    }
