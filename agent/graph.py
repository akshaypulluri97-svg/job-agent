from langgraph.graph import StateGraph, END, START
from agent.state import AgentState
from agent.nodes import extract_node, search_node, analyze_node, tailor_node


def build_graph():
    """Build and compile the LangGraph agent."""
    g = StateGraph(AgentState)

    g.add_node("extract", extract_node)
    g.add_node("search",  search_node)
    g.add_node("analyze", analyze_node)
    g.add_node("tailor",  tailor_node)

    g.add_edge(START, "extract")

    # If user pasted a target JD — skip search, go straight to analyze
    g.add_conditional_edges(
        "extract",
        lambda s: "analyze" if s.get("target_jd") else "search",
        {"analyze": "analyze", "search": "search"},
    )

    g.add_edge("search",  "analyze")
    g.add_edge("analyze", "tailor")
    g.add_edge("tailor",  END)

    return g.compile()
