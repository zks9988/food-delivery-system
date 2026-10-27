"""
Seed Demo Data
Creates sample users, merchants, menu items, and orders for demonstration.
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import SessionLocal, User, Merchant, MenuItem, Order, OrderItem, Review, RiderLocation
from auth import hash_password

def seed_demo_data():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(func.count(User.id)).scalar() > 5:
            print("[Seed] Data already exists, skipping...")
            return

        print("[Seed] Creating demo data...")

        # --- Users ---
        users_data = [
            {"username": "alice", "email": "alice@example.com", "password": "pass123", "role": "customer", "phone": "13800138001"},
            {"username": "bob", "email": "bob@example.com", "password": "pass123", "role": "rider", "phone": "13800138002"},
            {"username": "carol", "email": "carol@example.com", "password": "pass123", "role": "rider", "phone": "13800138003"},
            {"username": "chef_david", "email": "david@example.com", "password": "pass123", "role": "merchant", "phone": "13800138004"},
            {"username": "chef_emma", "email": "emma@example.com", "password": "pass123", "role": "merchant", "phone": "13800138005"},
            {"username": "analyst_fred", "email": "fred@example.com", "password": "pass123", "role": "analyst", "phone": "13800138006"},
            {"username": "regulator_grace", "email": "grace@example.com", "password": "pass123", "role": "regulator", "phone": "13800138007"},
            {"username": "henry", "email": "henry@example.com", "password": "pass123", "role": "customer", "phone": "13800138008"},
            {"username": "ivy", "email": "ivy@example.com", "password": "pass123", "role": "customer", "phone": "13800138009"},
        ]

        users = {}
        for ud in users_data:
            u = User(
                username=ud["username"],
                email=ud["email"],
                password_hash=hash_password(ud["password"]),
                role=ud["role"],
                phone=ud["phone"]
            )
            db.add(u)
            db.flush()
            users[ud["username"]] = u

        # --- Merchants ---
        merchants_data = [
            {"name": "Pizza Palace", "user": "chef_david", "cuisine": "Italian", "address": "123 Main St", "lat": 39.9042, "lng": 116.4074},
            {"name": "Noodle House", "user": "chef_emma", "cuisine": "Chinese", "address": "456 Oak Ave", "lat": 39.9142, "lng": 116.4174},
        ]

        merchants = {}
        for md in merchants_data:
            m = Merchant(
                user_id=users[md["user"]].id,
                name=md["name"],
                cuisine_type=md["cuisine"],
                address=md["address"],
                latitude=md["lat"],
                longitude=md["lng"],
                rating=4.0 + hash(md["name"]) % 10 / 10
            )
            db.add(m)
            db.flush()
            merchants[md["name"]] = m

        # --- Menu Items ---
        menu_items_data = [
            # Pizza Palace
            {"merchant": "Pizza Palace", "name": "Margherita Pizza", "price": 12.99, "category": "Pizza", "stock": 50},
            {"merchant": "Pizza Palace", "name": "Pepperoni Pizza", "price": 14.99, "category": "Pizza", "stock": 40},
            {"merchant": "Pizza Palace", "name": "Caesar Salad", "price": 8.99, "category": "Salad", "stock": 30},
            {"merchant": "Pizza Palace", "name": "Garlic Bread", "price": 4.99, "category": "Appetizer", "stock": 60},
            {"merchant": "Pizza Palace", "name": "Spaghetti Bolognese", "price": 11.99, "category": "Pasta", "stock": 35},
            {"merchant": "Pizza Palace", "name": "Tiramisu", "price": 6.99, "category": "Dessert", "stock": 25},
            # Noodle House
            {"merchant": "Noodle House", "name": "Beef Noodle Soup", "price": 10.99, "category": "Noodle", "stock": 45},
            {"merchant": "Noodle House", "name": "Dumplings (12pcs)", "price": 8.99, "category": "Appetizer", "stock": 50},
            {"merchant": "Noodle House", "name": "Kung Pao Chicken", "price": 12.99, "category": "Main", "stock": 35},
            {"merchant": "Noodle House", "name": "Fried Rice", "price": 9.99, "category": "Rice", "stock": 40},
            {"merchant": "Noodle House", "name": "Spring Rolls (6pcs)", "price": 5.99, "category": "Appetizer", "stock": 55},
            {"merchant": "Noodle House", "name": "Mapo Tofu", "price": 10.99, "category": "Main", "stock": 30},
        ]

        menu_items = {}
        for mid in menu_items_data:
            mi = MenuItem(
                merchant_id=merchants[mid["merchant"]].id,
                name=mid["name"],
                price=mid["price"],
                category=mid["category"],
                stock=mid["stock"]
            )
            db.add(mi)
            db.flush()
            menu_items[mid["name"]] = mi

        # --- Sample Orders (over the past 30 days) ---
        customers = [users["alice"], users["henry"], users["ivy"]]
        riders = [users["bob"], users["carol"]]
        now = datetime.now(timezone.utc)

        for days_ago in range(30, 0, -1):
            for _ in range(3):  # 3 orders per day
                customer = customers[hash(str(days_ago) + str(_)) % len(customers)]
                merchant = merchants[["Pizza Palace", "Noodle House"][hash(str(days_ago) + str(_) + "m") % 2]]
                rider = riders[hash(str(days_ago) + str(_) + "r") % len(riders)]
                statuses = ["delivered", "delivered", "delivered", "delivered", "cancelled"]
                status = statuses[hash(str(days_ago) + str(_) + "s") % len(statuses)]

                order_time = now - timedelta(days=days_ago, hours=hash(str(days_ago)) % 12)

                # Pick some items
                merchant_items = db.query(MenuItem).filter(MenuItem.merchant_id == merchant.id).all()
                if len(merchant_items) < 2:
                    continue
                item1 = merchant_items[hash(str(days_ago) + str(_) + "i1") % len(merchant_items)]
                item2 = merchant_items[hash(str(days_ago) + str(_) + "i2") % len(merchant_items)]

                total = item1.price * 1 + item2.price * 2

                order = Order(
                    customer_id=customer.id,
                    merchant_id=merchant.id,
                    rider_id=rider.id if status != "pending" else None,
                    status=status,
                    total_price=round(total, 2),
                    delivery_address=f"{100 + hash(str(days_ago)) % 900} Sample St",
                    delivery_latitude=39.90 + hash(str(days_ago)) % 100 / 1000,
                    delivery_longitude=116.40 + hash(str(days_ago)) % 100 / 1000,
                    payment_method=["cash", "card", "wechat"][hash(str(days_ago)) % 3],
                    created_at=order_time,
                    updated_at=order_time + timedelta(minutes=30)
                )
                db.add(order)
                db.flush()

                db.add(OrderItem(order_id=order.id, menu_item_id=item1.id, quantity=1, unit_price=item1.price))
                db.add(OrderItem(order_id=order.id, menu_item_id=item2.id, quantity=2, unit_price=item2.price))

                # Add reviews for delivered orders
                if status == "delivered":
                    review = Review(
                        order_id=order.id,
                        customer_id=customer.id,
                        merchant_id=merchant.id,
                        rating=3 + hash(str(days_ago) + str(_)) % 3,
                        content="Good food and fast delivery!" if hash(str(days_ago)) % 2 == 0 else "Decent experience overall.",
                        extra_meta={"delivery_time_min": 20 + hash(str(days_ago)) % 20}
                    )
                    db.add(review)

                # Add rider GPS data for delivered orders
                if status == "delivered" and rider:
                    for gps_point in range(5):
                        loc = RiderLocation(
                            rider_id=rider.id,
                            latitude=merchant.latitude + gps_point * 0.001,
                            longitude=merchant.longitude + gps_point * 0.001,
                            speed=15 + gps_point * 5,
                            extra_data={"simulated": True, "point": gps_point, "order_id": order.id},
                            recorded_at=order_time + timedelta(minutes=gps_point * 5)
                        )
                        db.add(loc)

        db.commit()
        print(f"[Seed] Created demo data successfully!")
        print(f"  - {len(users_data)} users")
        print(f"  - {len(merchants_data)} merchants")
        print(f"  - {len(menu_items_data)} menu items")
        print(f"  - Sample orders across 30 days")

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error: {e}")
        raise
    finally:
        db.close()
