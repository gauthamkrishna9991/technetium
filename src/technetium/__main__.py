import sys
from technetium.app import app, db

if __name__ == "__main__":
    if "--setup" in sys.argv:
        with app.app_context():
            db.create_all()
            db.session.commit()
            print("DATABASE TABLES CREATED")
    else:
        app.run(debug=True)
