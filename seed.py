from app import app, db, User
from werkzeug.security import generate_password_hash

def seed_users():
    with app.app_context():  # ✅ This line fixes the error
        db.create_all()  # Create tables if not exist

        users = [
            User(email="alice@example.com", password_hash=generate_password_hash("alice123")),
            User(email="bob@example.com", password_hash=generate_password_hash("bob123")),
            User(email="charlie@example.com", password_hash=generate_password_hash("charlie123"))
        ]

        db.session.add_all(users)
        db.session.commit()
        print("✅ Test users seeded.")

if __name__ == '__main__':
    seed_users()
