# Subtask 4.4: Agent Workflow Graph Construction

> **Task Reference:** `TASK-04` > `SUBTASK-4.4`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §7, `agent_rules/02-general-coding-guidelines.md` §4  

---

## 1. Description

Construct the complete LangGraph workflow in `src/agent/graph.py` linking the reasoning agent node, the tool execution node, and the conditional edge routing.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/agent/graph.py`
- State Graph Definition:
  ```python
  from langgraph.graph import StateGraph, START, END
  from langgraph.prebuilt import ToolNode, tools_condition
  from src.agent.state import AgentState

  def create_agent_graph(llm_client, tools: list[Any], checkpointer):
      workflow = StateGraph(AgentState)
      
      # Bind tools to LLM
      llm_with_tools = llm_client.bind_tools(tools)
      
      # Define reasoning node
      async def call_model(state: AgentState) -> dict[str, Any]:
          response = await llm_with_tools.ainvoke(state["messages"])
          return {"messages": [response]}
      
      # Add nodes
      workflow.add_node("agent", call_model)
      workflow.add_node("tools", ToolNode(tools))
      
      # Add edges
      workflow.add_edge(START, "agent")
      workflow.add_conditional_edges("agent", tools_condition)
      workflow.add_edge("tools", "agent")
      
      return workflow.compile(checkpointer=checkpointer)
  ```
- Tool list includes:
  - `web_search`
  - `propose_file_write` (defined in Task 5)

---

## 3. Verification

Create unit test `tests/unit/test_agent_graph.py`:
1. Invoke graph with simple question: goes START -> agent -> END directly.
2. Invoke graph requiring web search: goes START -> agent -> tools (web_search) -> agent -> END.
