"""
Session Storage Service
Stores session data, human responses, and forecast history

This is an in-memory implementation that can be replaced with a database
for production use.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SessionStorage:
    """
    In-memory storage for session data and human responses.

    Stores:
    1. Session data (analysis results)
    2. Human responses (question answers, scenario selections)
    3. Forecast history (original and revised forecasts)

    Note: This is a singleton to maintain state across requests.
    For production, replace with Redis or database storage.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize storage containers"""
        # Session data: {session_id: {analysis_result}}
        self.sessions: Dict[str, Dict[str, Any]] = {}

        # Human responses: {session_id: [responses]}
        self.responses: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Forecast history: {project_id: [{timestamp, forecasts}]}
        self.forecast_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # Approved scenarios: {session_id: scenario_data}
        self.approved_scenarios: Dict[str, Dict[str, Any]] = {}

        logger.info("SessionStorage initialized")

    def store_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session analysis result"""
        self.sessions[session_id] = {
            **data,
            'stored_at': datetime.utcnow().isoformat() + 'Z'
        }
        logger.info(f"Stored session: {session_id}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        return self.sessions.get(session_id)

    def store_response(
        self,
        session_id: str,
        question_id: str,
        response_value: str,
        reason_codes: Optional[List[Dict[str, Any]]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store human response to a question.

        Args:
            session_id: The session this response belongs to
            question_id: The question being answered
            response_value: The selected option value
            reason_codes: Optional reason codes with percentages
            notes: Optional free-text notes

        Returns:
            The stored response record
        """
        response = {
            'question_id': question_id,
            'response_value': response_value,
            'reason_codes': reason_codes or [],
            'notes': notes,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        self.responses[session_id].append(response)
        logger.info(f"Stored response for session {session_id}, question {question_id}")
        return response

    def get_responses(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all responses for a session"""
        return self.responses.get(session_id, [])

    def approve_scenario(
        self,
        session_id: str,
        scenario_id: str,
        reason_codes: List[Dict[str, Any]],
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store approved scenario selection.

        Args:
            session_id: The session this approval belongs to
            scenario_id: The selected scenario ID
            reason_codes: Reason codes with percentages (must sum to 100)
            notes: Optional notes from user

        Returns:
            The approval record
        """
        # Validate reason code percentages sum to 100
        total_percent = sum(rc.get('percent', 0) for rc in reason_codes)
        if reason_codes and total_percent != 100:
            logger.warning(f"Reason code percentages sum to {total_percent}, not 100")

        approval = {
            'session_id': session_id,
            'scenario_id': scenario_id,
            'reason_codes': reason_codes,
            'notes': notes,
            'approved_at': datetime.utcnow().isoformat() + 'Z',
            'status': 'approved'
        }

        self.approved_scenarios[session_id] = approval
        logger.info(f"Scenario {scenario_id} approved for session {session_id}")
        return approval

    def get_approved_scenario(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get approved scenario for a session"""
        return self.approved_scenarios.get(session_id)

    def store_forecast_history(
        self,
        project_id: str,
        forecasts: List[Dict[str, Any]],
        revision_type: str = 'ai_generated'
    ) -> None:
        """
        Store forecast revision in history.

        Args:
            project_id: The project ID
            forecasts: List of monthly forecasts
            revision_type: 'original', 'ai_generated', 'human_approved'
        """
        record = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'revision_type': revision_type,
            'forecasts': forecasts
        }
        self.forecast_history[project_id].append(record)
        logger.info(f"Stored forecast history for project {project_id}")

    def get_forecast_history(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all forecast revisions for a project"""
        return self.forecast_history.get(project_id, [])

    def get_learning_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get data for agent learning from human responses.

        Returns recent sessions with their human responses for analysis.
        This data can be used to improve future recommendations.
        """
        learning_data = []

        for session_id, session_data in list(self.sessions.items())[-limit:]:
            responses = self.responses.get(session_id, [])
            approved = self.approved_scenarios.get(session_id)

            if responses or approved:
                learning_data.append({
                    'session_id': session_id,
                    'original_flags': session_data.get('flags', []),
                    'original_scenarios': session_data.get('scenarios', []),
                    'human_responses': responses,
                    'approved_scenario': approved
                })

        return learning_data

    def clear_session(self, session_id: str) -> None:
        """Clear all data for a session"""
        self.sessions.pop(session_id, None)
        self.responses.pop(session_id, None)
        self.approved_scenarios.pop(session_id, None)
        logger.info(f"Cleared session: {session_id}")

    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics"""
        return {
            'total_sessions': len(self.sessions),
            'total_responses': sum(len(r) for r in self.responses.values()),
            'total_approvals': len(self.approved_scenarios),
            'projects_with_history': len(self.forecast_history)
        }


# Singleton instance
session_storage = SessionStorage()
