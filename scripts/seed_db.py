"""Seed the database with sample products so the demo has something to sell.

Usage: python -m scripts.seed_db
"""
from app.db.models import Product
from app.db.session import get_session, init_db

SAMPLE_PRODUCTS = [
    ("Rice Cooker 1.8L", "Digital rice cooker, 1.8 liter capacity, non-stick pot.", 349_000, 25),
    ("Electric Kettle 1.5L", "Stainless steel electric kettle with auto shut-off.", 189_000, 40),
    ("Non-stick Frying Pan 24cm", "Marble-coated non-stick frying pan, induction-ready.", 129_000, 60),
    ("Vacuum Flask 1L", "Double-wall stainless vacuum flask, keeps drinks hot for 12h.", 99_000, 80),
    ("Bamboo Cutting Board Set", "Set of 3 bamboo cutting boards, different sizes.", 79_000, 50),
]


def main() -> None:
    init_db()
    with get_session() as db:
        for name, description, price, stock in SAMPLE_PRODUCTS:
            existing = db.query(Product).filter_by(name=name).first()
            if existing:
                continue
            db.add(Product(name=name, description=description, price=price, stock=stock))
    print(f"Seeded {len(SAMPLE_PRODUCTS)} products (skipping any that already existed).")


if __name__ == "__main__":
    main()
