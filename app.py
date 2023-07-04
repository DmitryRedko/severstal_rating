from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from user import UserManager,AdminManager
from config import dictionary, db_settings
from database import DataBase

class FlaskApp:
    def __init__(self):
        self.db = DataBase(db_settings)
        self.app = Flask(__name__)
        self.jinja_env = self.app.jinja_env
        self.jinja_env.add_extension('jinja2.ext.loopcontrols')
        self.app.secret_key = 'your_secret_key'
        self.user_manager = UserManager(self.db)
        self.admin_manager = AdminManager(dictionary)

        self.app.route('/')(self.home)
        self.app.route('/login', methods=['GET', 'POST'])(self.login)
        self.app.route('/admin', methods=['GET', 'POST'])(self.admin)
        self.app.route('/dashboard', methods=['GET', 'POST'])(self.dashboard)
        self.app.route('/dashboard_admin', methods=['GET', 'POST'])(self.dashboard_admin)
        self.app.route('/colleague_page/<string:colleague_num>', methods=['GET', 'POST'])(self.colleague_page)
        self.app.route('/logout')(self.logout)

    def run(self):
        self.app.run(debug=True, port=5000)

    def home(self):
        return render_template('base/index.html')

    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if self.user_manager.verify_user(username, password):
                session['username'] = username
                session['password'] = password  # Сохраняем пароль в сеансе
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('dashboard/login.html', error=error)
        return render_template('dashboard/login.html')

    def admin(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(username,password)
            if self.admin_manager.verify_admin(username, password):
                session['username'] = username
                return redirect(url_for('dashboard_admin'))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('admin/admin.html', error=error)
        return render_template('admin/admin.html')

    def dashboard(self, password = None):
        if password is None:
             password = session.get('password')
        
        self.db = DataBase(db_settings)
        colleagues = self.db.get_colleagues(password,0)
        username = self.db.get_num_record_userinfo(password)['full_name']
        return render_template('dashboard/dashboard.html', username=username, colleagues_list=colleagues)
    
    def colleague_page(self, colleague_num):
        criterias = self.db.get_criterias_name(colleague_num)
        description_list = [row[1] for row in criterias]
        criterias_list = [row[0] for row in criterias]
        userinfo = (self.db.get_num_record_userinfo(colleague_num))

        return render_template('dashboard/colleague_page.html', description_list=description_list, criterias_list=criterias_list, userinfo = userinfo)

    def dashboard_admin(self):
        username= 'admin'
        password = 'admin'
        colleagues = self.db.get_colleagues(password,1)
        return render_template('admin/dashboard_admin.html', username=username, colleagues_list=colleagues)

    def logout(self):
        session.pop('username', None)
        return redirect(url_for('home'))

    @staticmethod
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
