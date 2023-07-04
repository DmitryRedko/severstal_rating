
class UserManager:
    def __init__(self,db):
        self.users = db.get_head_colleagues()

    def verify_user(self, username, password):
        return username in self.users and self.users[username] == password

    def is_username_taken(self, username):
        return username in self.users

    def add_user(self, username, password):
        self.users[username] = password

class AdminManager:
    def __init__(self,dictionary):
        self.admin = dictionary

    def verify_admin(self, adminname, password):
        return adminname in self.admin and self.admin[adminname] == password

    def is_adminname_taken(self, adminname):
        return adminname in self.admin

    def add_admin(self, adminname, password):
        self.users[adminname] = password

        