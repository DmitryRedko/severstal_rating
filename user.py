class UserManager:
    def __init__(self):
        self.users = {
            'john': 'password123',
            'mary': 'abc123'
        }

    def verify_user(self, username, password):
        return username in self.users and self.users[username] == password

    def is_username_taken(self, username):
        return username in self.users

    def add_user(self, username, password):
        self.users[username] = password
