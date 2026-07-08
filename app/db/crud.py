from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Customer, Message, Order, OrderStatus, Product


def get_or_create_customer(db: Session, wa_id: str, name: str | None = None) -> Customer:
    customer = db.get(Customer, wa_id)
    if customer is None:
        customer = Customer(wa_id=wa_id, name=name)
        db.add(customer)
        db.flush()
    elif name and not customer.name:
        customer.name = name
    return customer


def save_message(db: Session, wa_id: str, role: str, content: str) -> Message:
    message = Message(customer_wa_id=wa_id, role=role, content=content)
    db.add(message)
    db.flush()
    return message


def get_recent_messages(db: Session, wa_id: str, limit: int = 10) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.customer_wa_id == wa_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return list(reversed(db.execute(stmt).scalars().all()))


def find_product_by_name(db: Session, name: str) -> Product | None:
    stmt = select(Product).where(Product.name.ilike(f"%{name}%")).limit(1)
    return db.execute(stmt).scalars().first()


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def create_order(db: Session, wa_id: str, product: Product, quantity: int) -> Order:
    order = Order(customer_wa_id=wa_id, product_id=product.id, quantity=quantity)
    db.add(order)
    product.stock = max(product.stock - quantity, 0)
    db.flush()
    return order


def update_order_status(db: Session, order_id: int, status: OrderStatus) -> Order | None:
    order = db.get(Order, order_id)
    if order is not None:
        order.status = status
        db.flush()
    return order


def set_payment_proof(db: Session, order_id: int, media_id: str, ocr_text: str) -> Order | None:
    order = db.get(Order, order_id)
    if order is not None:
        order.payment_proof_media_id = media_id
        order.payment_ocr_text = ocr_text
        order.status = OrderStatus.PAYMENT_SUBMITTED
        db.flush()
    return order


def latest_order_for_customer(db: Session, wa_id: str) -> Order | None:
    stmt = (
        select(Order)
        .where(Order.customer_wa_id == wa_id)
        .order_by(Order.created_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalars().first()
