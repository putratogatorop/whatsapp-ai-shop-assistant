from langchain_core.tools import StructuredTool, tool

from app.db.crud import (
    create_order,
    find_product_by_name,
    get_order,
)
from app.db.session import get_session
from app.integrations.n8n_notify import notify_admin
from app.rag.retriever import search_knowledge_base as _search_knowledge_base


@tool
def search_knowledge_base(query: str) -> str:
    """Search the store's FAQ / policy knowledge base (shipping, returns, payment,
    general info) for information relevant to the customer's question."""
    return _search_knowledge_base(query)


@tool
def check_stock(product_name: str) -> str:
    """Look up a product by (partial) name and report its price and stock level."""
    with get_session() as db:
        product = find_product_by_name(db, product_name)
        if product is None:
            return f"No product matching '{product_name}' was found."
        if product.stock <= 0:
            return f"{product.name} is currently out of stock."
        return f"{product.name}: Rp{product.price:,.0f}, {product.stock} in stock."


@tool
def check_order_status(order_id: int) -> str:
    """Look up an order by its numeric order ID and report its current status."""
    with get_session() as db:
        order = get_order(db, order_id)
        if order is None:
            return f"No order found with ID {order_id}."
        return f"Order #{order.id}: status={order.status.value}, quantity={order.quantity}."


def _make_create_order_tool(wa_id: str) -> StructuredTool:
    def _create_order(product_name: str, quantity: int = 1) -> str:
        """Create a new order for the current customer for the given product and quantity."""
        with get_session() as db:
            product = find_product_by_name(db, product_name)
            if product is None:
                return f"No product matching '{product_name}' was found, cannot create order."
            if product.stock < quantity:
                return f"Only {product.stock} of {product.name} left in stock, cannot order {quantity}."
            order = create_order(db, wa_id=wa_id, product=product, quantity=quantity)
            return (
                f"Order #{order.id} created for {quantity}x {product.name} "
                f"(Rp{product.price * quantity:,.0f} total). Awaiting payment."
            )

    return StructuredTool.from_function(
        func=_create_order,
        name="create_order",
        description="Create a new order for the current customer for a given product and quantity.",
    )


def _make_escalate_tool(wa_id: str) -> StructuredTool:
    def _escalate(reason: str) -> str:
        """Escalate the conversation to a human agent, with a short reason."""
        notify_admin("escalation", {"wa_id": wa_id, "reason": reason})
        return "I've flagged this conversation for a human team member — they'll follow up shortly."

    return StructuredTool.from_function(
        func=_escalate,
        name="escalate_to_human",
        description="Escalate the conversation to a human agent when the assistant cannot help.",
    )


def build_tools(wa_id: str) -> list:
    """Tools bound to the current customer's wa_id (needed for create_order/escalate)."""
    return [
        search_knowledge_base,
        check_stock,
        check_order_status,
        _make_create_order_tool(wa_id),
        _make_escalate_tool(wa_id),
    ]
