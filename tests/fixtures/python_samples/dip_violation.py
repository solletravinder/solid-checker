"""Sample file with DIP violation - concrete dependency."""

class MySQLDatabase:
    def connect(self): pass
    def query(self, sql): pass

class UserRepository:
    def __init__(self):
        self.db = MySQLDatabase()

    def find_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")
