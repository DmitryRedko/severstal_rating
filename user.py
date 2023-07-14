from flask_login import UserMixin
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


class UserLogin(UserMixin):
    def get_user_from_DB(self, user_id, db):
        self.__user = db.get_num_record_userinfo(user_id)
        return self
        
    def create(self, user):
        self.__user = user
        return self
     
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.__user)