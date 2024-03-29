from flask_login import UserMixin
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash

class UserManager:
    def __init__(self, db):
        self.db = db

    def __update_info(self):
        users = self.db.get_auterisation_info()
        self.users = {}
        for val in users:
            self.users[val[0]] = val[1]

    def verify_user(self, username, password):
        self.__update_info()
        return username in self.users and check_password_hash(self.users[username],password)

    def is_username_taken(self, username):
        return username in self.users

    def add_user(self, username, password):
        self.users[username] = password

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


class AdminManager(UserLogin):
    def __init__(self, dictionary):
        self.admin = dictionary

    def verify_admin(self, adminname, password):
        return adminname in self.admin and self.admin[adminname] == password
    
    def login_admin(self, adminname, password):
        if self.verify_admin(adminname, password):
            user = self.create(adminname)  
            login_user(user)  
            return True
        return False

    def logout_admin(self):
        logout_user()
