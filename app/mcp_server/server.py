"""Bonus: expose the store's read-only tools over MCP (stdio transport).

This lets any MCP client (Claude Desktop, the `mcp` CLI inspector, another
agent) call check_stock / check_order_status / search_knowledge_base directly,
independent of the WhatsApp channel -- demonstrates the same tool layer being
reusable outside of the LangGraph agent, which is the whole point of MCP.

Run with:  python -m app.mcp_server.server
"""
from mcp.server.fastmcp import FastMCP

from app.db.crud import find_product_by_name, get_order
from app.db.session import get_session
from app.rag.retriever import search_knowledge_base as _search_knowledge_base

mcp = FastMCP("whatsapp-shop-assistant")


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search the store's FAQ / policy knowledge base."""
    return _search_knowledge_base(query)


@mcp.tool()
def check_stock(product_name: str) -> str:
    """Look up a product by (partial) name and report price and stock level."""
    with get_session() as db:
        product = find_product_by_name(db, product_name)
        if product is None:
            return f"No product matching '{product_name}' was found."
        return f"{product.name}: Rp{product.price:,.0f}, {product.stock} in stock."


@mcp.tool()
def check_order_status(order_id: int) -> str:
    """Look up an order by its numeric order ID and report its current status."""
    with get_session() as db:
        order = get_order(db, order_id)
        if order is None:
            return f"No order found with ID {order_id}."
        return f"Order #{order.id}: status={order.status.value}, quantity={order.quantity}."


if __name__ == "__main__":
    mcp.run(transport="stdio")
