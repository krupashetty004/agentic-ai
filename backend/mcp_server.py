from mcp.server.fastmcp import FastMCP
from app.services.mcp_tools import (
    get_source_record as get_source_record_tool,
    list_knowledge_sources as list_knowledge_sources_tool,
    search_knowledge as search_knowledge_tool,
)

mcp = FastMCP("Agentic AI Knowledge Tools")


@mcp.tool()
def list_knowledge_sources():
    """List the local knowledge sources available to the agent."""
    return list_knowledge_sources_tool()


@mcp.tool()
def search_knowledge(query: str, limit: int = 5):
    """Search the local AI tooling catalog for relevant records."""
    return search_knowledge_tool(query, limit)


@mcp.tool()
def get_source_record(title: str):
    """Return one knowledge record by its title."""
    return get_source_record_tool(title)


if __name__ == "__main__":
    mcp.run()
