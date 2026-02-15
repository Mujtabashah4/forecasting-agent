"""
Node 8: Generate Explanation
Uses LLM to generate human-readable explanation
"""
from app.agent.state import ForecastAgentState
import asyncio
import httpx
from app.config import settings
from app.utils.sanitization import sanitize_project_name
import logging

logger = logging.getLogger(__name__)


async def generate_explanation_node(state: ForecastAgentState) -> ForecastAgentState:
    """
    Use LLM to generate human-readable explanation.

    This node calls the Ollama/Qwen LLM service with context.
    Falls back to rule-based explanation if LLM is unavailable.
    """
    # Build context for LLM (with sanitization)
    raw_project_name = state['project'].get('name', 'Unknown')
    safe_project_name = sanitize_project_name(raw_project_name)

    context = {
        'project_name': safe_project_name,
        'budget': state['total_budget'],
        'approved': state['total_approved'],
        'total_actuals': state['total_actuals'],
        'budget_consumption': state['budget_consumption_percent'],
        'nov': state['net_order_value'],
        'variances': state['variances'],
        'flags': state['flags'],
        'scenarios': state['scenarios']
    }

    # Build prompt with sanitized inputs
    prompt = f"""You are a financial analyst explaining project forecast analysis to a project manager.

Project: {context['project_name']}
Budget: ${context['budget']:,.2f}
Approved Amount: ${context['approved']:,.2f}
Total Actuals to Date: ${context['total_actuals']:,.2f}
Budget Consumption: {context['budget_consumption']:.1f}%
Net Order Value (remaining obligations): ${context['nov']:,.2f}

Issues Found:
{_format_flags(context['flags'])}

Scenarios Generated:
{_format_scenarios(context['scenarios'])}

Write a clear, concise explanation (3-4 sentences) that:
1. Summarizes the current state of the project
2. Highlights the main issues found
3. Explains what the scenarios mean
4. Provides a recommendation

Keep it simple and actionable. Do not use technical jargon."""

    # Try to call LLM service
    try:
        explanation = await _call_llm_async(prompt)
        if explanation and len(explanation) > 20:
            state['explanation'] = explanation
            logger.info("LLM explanation generated successfully")
        else:
            state['explanation'] = _generate_simple_explanation(context)
            logger.info("Using fallback explanation (short LLM response)")
    except Exception as e:
        logger.warning(f"LLM call failed, using fallback: {str(e)}")
        state['explanation'] = _generate_simple_explanation(context)

    # Generate summary
    summary = f"Budget analysis for {context['project_name']}: {context['budget_consumption']:.1f}% consumed, {len(context['flags'])} issues detected."
    state['summary'] = summary

    return state


async def _call_llm_async(prompt: str) -> str:
    """
    Call Ollama LLM asynchronously.

    Uses httpx async client to make the API call without blocking event loop.
    """
    try:
        async with httpx.AsyncClient(timeout=float(settings.LLM_TIMEOUT)) as client:
            response = await client.post(
                f"{settings.OLLAMA_HOST}/api/generate",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "prompt": prompt,
                    "temperature": settings.LLM_TEMPERATURE,
                    "stream": False
                }
            )
            response.raise_for_status()
            return response.json().get("response", "")
    except httpx.TimeoutException:
        logger.warning("LLM request timed out")
        return ""
    except httpx.HTTPError as e:
        logger.warning(f"LLM HTTP error: {str(e)}")
        return ""
    except Exception as e:
        logger.warning(f"LLM call error: {str(e)}")
        return ""


def _format_flags(flags):
    """Format flags for prompt"""
    if not flags:
        return "None"
    return "\n".join([f"- {f['message']}" for f in flags])


def _format_scenarios(scenarios):
    """Format scenarios for prompt"""
    if not scenarios:
        return "None"
    return "\n".join([f"- {s['name']}: {s['description']}" for s in scenarios])


def _generate_simple_explanation(context):
    """Generate simple explanation without LLM (fallback)"""
    consumption = context['budget_consumption']
    flag_count = len(context['flags'])

    if consumption < 25:
        phase = "early stages"
    elif consumption < 50:
        phase = "on track"
    elif consumption < 75:
        phase = "mid-way through"
    elif consumption < 90:
        phase = "nearing completion"
    else:
        phase = "at critical budget threshold"

    if flag_count == 0:
        status = "progressing smoothly with no significant issues"
    elif flag_count == 1:
        status = "has one issue requiring attention"
    else:
        status = f"has {flag_count} issues that need review"

    return f"The project is {phase} with {consumption:.1f}% of budget consumed. It {status}. Review the scenarios provided to determine the best path forward."
