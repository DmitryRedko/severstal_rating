from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from user import UserManager,AdminManager
from config import dictionary, db_settings
from database import DataBase
import datetime

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
        self.app.route('/colleague_page/<string:colleague_num>/<string:head_num>', methods=['GET', 'POST'])(self.colleague_page)
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
    
    def __get_mark_list(self,colleague_num, name, userinfo, date):
        criterias= self.db.get_criterias_name_named_block(colleague_num,name)
        criterias_list = [row[0] for row in criterias]
        mark_msgs= []
        marks = []
        flag = 0
        status = 0
        for i in range(len(criterias_list)):
            mark=0
            if(name =='first'):
                mark = request.form.get(f"markf_{i}")
                print("MARK:", mark)
                mark_msgs.append(request.form.get(f"messf_{i}"))
                print("MESS:", mark_msgs)
            else:
                mark = request.form.get(f"marks_{i}")
                mark_msgs.append(request.form.get(f"messs_{i}"))

            if(mark!='' and mark is not None):
                marks.append(float(mark))
            else:
                flag = 1
                break    
        print(len(marks), len(criterias_list))
        if(len(marks)==len(criterias_list) and flag == 0):
            status = 1
        listmark = []
        if(flag ==0 and status ==1):
            for i in range(len(criterias_list)):
                listmark.append([userinfo['employee_record_card'],criterias_list[i],date,marks[i],mark_msgs[i]])
        return listmark, status
                
        
    def colleague_page(self, colleague_num, head_num):
        listmark_first,listmark_second,status = [],[],0
        status_msg=''
        userinfo = self.db.get_num_record_userinfo(colleague_num)  
        date = datetime.date.today().strftime("%d.%m.%Y")
        
        if request.method == 'POST' and "submit_button" in request.form:
            listmark_first, status_first =  self.__get_mark_list(colleague_num, 'first', userinfo, date)
            listmark_second, status_second =  self.__get_mark_list(colleague_num, 'second', userinfo, date)
            print(status_first, status_second)
            if(status_first == 1 and status_second == 1):
                status_msg = 'Результаты успешно сохранены.'
                self.db.add_mark_to_base(listmark_first, 'first')
                self.db.add_mark_to_base(listmark_second, 'second')
                self.db.update_rating_status(colleague_num,head_num,1)
                status = 1
            else:
                status_msg = 'Пожалуйста, заполните все доступные критери.'

        info_first = self.db.get_criterias_name_named_block(colleague_num,'first')
        info_second = self.db.get_criterias_name_named_block(colleague_num,'second')
        print_info_first = enumerate([[row[0],row[1],date,row[2],row[3]] for row in info_first])
        print_info_second = enumerate([[row[0],row[1],date,row[2],row[3]] for row in info_second])

        return render_template('dashboard/colleague_page.html', 
                                print_info_first=print_info_first,
                                print_info_second=print_info_second,
                                userinfo=userinfo,
                                date=date,
                                status_msg = status_msg,
                                status = status)


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
