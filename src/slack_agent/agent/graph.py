from __future__ import annotations

from typing import Any

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from slack_agent.agent.prompts import SYSTEM_PROMPT
from slack_agent.agent.state import AgentState
from slack_agent.agent.tools.chart import generate_chart
from slack_agent.agent.tools.fetch import fetch_web_page
from slack_agent.agent.tools.search import web_search
from slack_agent.agent.tools.write_gate import propose_file_write


def create_agent_graph(
    llm_client: Any,
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    """Build and compile the LangGraph workflow for autonomous Slack AI assistance."""
    tools = [web_search, fetch_web_page, generate_chart, propose_file_write]
    llm_with_tools = llm_client.bind_tools(tools)

    async def call_model(state: AgentState) -> dict[str, Any]:
        """Reasoning node that runs the LLM with system prompt and message history."""
        messages = list(state.get("messages", []))
        # Ensure system prompt is present at start of conversation
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=checkpointer)
