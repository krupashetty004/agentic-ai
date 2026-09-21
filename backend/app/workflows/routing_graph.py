from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.agents.supervisor_agent import SupervisorAgent


class RoutingState(TypedDict):
    message: str
    route: str
    feedback_hint: str


class RoutingGraph:
    """Explicit LangGraph orchestration for supervisor routing."""

    def __init__(self, supervisor: SupervisorAgent) -> None:
        self.supervisor = supervisor
        graph = StateGraph(RoutingState)
        graph.add_node("supervisor", self._supervisor_node)
        graph.add_node("greeting", self._route_node)
        graph.add_node("search", self._route_node)
        graph.add_node("summary", self._route_node)
        graph.add_node("parallel", self._route_node)
        graph.set_entry_point("supervisor")
        graph.add_conditional_edges(
            "supervisor",
            lambda state: state["route"],
            {
                "greeting": "greeting",
                "search": "search",
                "summary": "summary",
                "parallel": "parallel",
            },
        )
        for route in ("greeting", "search", "summary", "parallel"):
            graph.add_edge(route, END)
        self.compiled = graph.compile()

    async def _supervisor_node(self, state: RoutingState) -> RoutingState:
        route = await self.supervisor.decide_route(state["message"])
        if state.get("feedback_hint") == "grounded" and route == "summary":
            route = "parallel"
        return {**state, "route": route}

    async def _route_node(self, state: RoutingState) -> RoutingState:
        return state

    async def decide(self, message: str, feedback_hint: str = "") -> str:
        result = await self.compiled.ainvoke(
            {"message": message, "route": "parallel", "feedback_hint": feedback_hint}
        )
        return result["route"]
