"""
LangGraph state definitions.

AxiomCartState       – the main graph state shared by all nodes.
WorkerInput          – the payload sent to agent workers via Send().
AgentTask            – structured routing output from the orchestrator.
ClassificationResult – orchestrator's full decision.
"""

from __future__ import annotations

import operator
from typing import Annotated, List, Literal, TypedDict

from langchain_core.messages import AnyMessage
from pydantic import BaseModel, Field


def agent_results_reducer(current: list[dict], update: list[dict]) -> list[dict]:
    """Like operator.add, but an empty list signals a reset."""
    if not update:
        return []
    return current + update


class AgentTask(BaseModel):
    """A single task assigned to a specialist agent."""

    agent: Literal["product_agent", "support_agent"] = Field(
        description="Which agent handles this task"
    )
    task_description: str = Field(
        description="What the agent should do"
    )


class ClassificationResult(BaseModel):
    """Orchestrator's routing decision."""

    tasks: List[AgentTask] = Field(description="Tasks to dispatch")
    requires_synthesis: bool = Field(
        description="True when multiple agents must have their results merged"
    )
    reasoning: str = Field(description="Brief explanation of routing decision")


class AxiomCartState(TypedDict):
    """Top-level state that flows through the entire graph."""

    # Conversation
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str

    # Routing
    tasks: list[AgentTask]
    requires_synthesis: bool

    # Collected results from agents (operator.add merges parallel results)
    agent_results: Annotated[list[dict], agent_results_reducer]

    # Final response returned to the user
    final_answer: str


class WorkerInput(TypedDict):
    """Payload delivered to an agent worker node via Send().

    NOTE: This is intentionally flat — no nested Pydantic objects —
    so that Send() serialisation works without surprises.
    """

    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    task_description: str
