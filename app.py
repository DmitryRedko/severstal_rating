from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from functools import wraps
from user import UserManager,AdminManager, UserLogin
from config import dictionary, db_settings
from database import DataBase
import datetime

class FlaskApp():
    def __init__(self):
        self.db = DataBase(db_settings)
        self.app = Flask(__name__)
        self.login_manager = LoginManager(self.app)
        self.login_manager.user_loader(self.load_user)
        self.jinja_env = self.app.jinja_env
        self.jinja_env.add_extension('jinja2.ext.loopcontrols')
        self.app.secret_key = 'your_secret_key'
        self.user_manager = UserManager(self.db)
        self.admin_manager = AdminManager(dictionary)

        self.app.route('/')(self.home)
        self.app.route('/login', methods=['GET', 'POST'])(self.login)
        self.app.route('/admin', methods=['GET', 'POST'])(self.admin)
        self.app.route('/dashboard_admin', methods=['GET', 'POST'])(self.dashboard_admin)
        self.app.route('/dashboard/<string:head_id>', methods=['GET', 'POST'])(self.dashboard)
        self.app.route('/dashboard_rated/<string:head_id>', methods=['GET', 'POST'])(self.dashboard_rated)
        self.app.route('/dashboard_to_rate/<string:head_id>', methods=['GET', 'POST'])(self.dashboard_to_rate)
        self.app.route('/colleague_page/<string:colleague_id>/<string:head_id>', methods=['GET', 'POST'])(self.colleague_page)
        self.app.route('/colleague_page_rated/<string:colleague_id>/<string:head_id>', methods=['GET', 'POST'])(self.colleague_page_rated)
        self.app.route('/logout')(self.logout)
    
    def run(self):
        self.app.run(debug=True, port=5000)

    def home(self):
        return render_template('base/index.html')

    def login(self):
        # if current_user.is_authenticated:
        #     print(current_user.get_id())
        #     return render_template('dashboard/dashboard.html', head_id=current_user.get_id())
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if self.user_manager.verify_user(username, password):
                user_id = self.db.get_num_record_userinfo(password)['user_id']
                print(user_id)
                user_login = UserLogin().create(user_id)
                login_user(user_login)
                session['username'] = username
                session['password'] = password
                print("HERE")
                return redirect(url_for('dashboard', head_id=user_id))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('dashboard/login.html', error=error)
        return render_template('dashboard/login.html')

    def load_user(self, user_id):
        print("load_user")
        return UserLogin().get_user_from_DB(user_id, self.db)

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

    @login_required
    def dashboard(self, head_id):
        print(head_id)
        self.db = DataBase(db_settings)
        head_info = self.db.get_id_userinfo(head_id)
        print(head_info)
        colleagues = self.db.get_colleagues(head_info['employee_record_card'])
        print()
        print(colleagues)
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template('dashboard/dashboard.html', username=head_username, colleagues_list=colleagues, head_id = head_id)
    
    @login_required
    def dashboard_rated(self, head_id):
        print(head_id)
        self.db = DataBase(db_settings)
        head_info = self.db.get_id_userinfo(head_id)
        print(head_info)
        colleagues = self.db.get_colleagues_rated(head_info['employee_record_card'])
        print()
        print(colleagues)
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template('dashboard/dashboard_rated.html', username=head_username, colleagues_list=colleagues, head_id = head_id)
    
    @login_required
    def dashboard_to_rate(self, head_id):
        print(head_id)
        self.db = DataBase(db_settings)
        head_info = self.db.get_id_userinfo(head_id)
        print(head_info)
        colleagues = self.db.get_colleagues_to_rate(head_info['employee_record_card'])
        print()
        print(colleagues)
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template('dashboard/dashboard_to_rate.html', username=head_username, colleagues_list=colleagues, head_id = head_id)
    
    
    
    def __get_mark_list(self,colleague_num, name, userinfo, date):
        criterias= self.db.get_criterias_name_named_block(colleague_num,name)
        criterias_list, min_score, max_score, description = [],[],[],[]
        print(criterias)
        for row in criterias:
            criterias_list.append(row[0])
            description.append(row[1])
            min_score.append(row[2])
            max_score.append(row[3])
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
                listmark.append([userinfo['employee_record_card'],criterias_list[i], description[i] ,date, min_score[i], max_score[i], marks[i], mark_msgs[i]])
        return listmark, status
                
    @login_required
    def colleague_page(self, colleague_id, head_id):
        listmark_first,listmark_second,status = [],[],0
        status_msg=''
        userinfo = self.db.get_id_userinfo(colleague_id)
        date = datetime.date.today().strftime("%d.%m.%Y")
        if request.method == 'POST' and "submit_button" in request.form:
            listmark_first, status_first =  self.__get_mark_list(colleague_id, 'first', userinfo, date)
            listmark_second, status_second =  self.__get_mark_list(colleague_id, 'second', userinfo, date)
            if(status_first == 1 and status_second == 1 and self.db.get_rating_status(colleague_id,head_id) == 0):
                status1 = self.db.add_mark_to_base(listmark_first, 'first')
                status2 = self.db.add_mark_to_base(listmark_second, 'second')
                if (status1 and status2):
                    flash('Результаты успешно сохранены.', category = 'success')
                else:
                    flash('Ошибка добавления данных в базу.', category = 'error')
                self.db.update_rating_status(colleague_id,head_id,1)
                status = 1
            elif(status_first == 0 or status_second == 0):
                flash( 'Пожалуйста, заполните все доступные критери.', category = 'error')
            else:
                flash( 'Вы уже оценили данного сотрудника.', category = 'error')
                
        info_first = self.db.get_criterias_name_named_block(colleague_id,'first')
        info_second = self.db.get_criterias_name_named_block(colleague_id,'second')
        print_info_first = enumerate([[row[0],row[1],date,row[2],row[3]] for row in info_first])
        print_info_second = enumerate([[row[0],row[1],date,row[2],row[3]] for row in info_second])

        return render_template('dashboard/colleague_page.html', 
                                print_info_first=print_info_first,
                                print_info_second=print_info_second,
                                userinfo=userinfo,
                                date=date,
                                status_msg = status_msg,
                                status = status,
                                colleague_id=colleague_id,
                                head_id=head_id
                                )
  
    @login_required
    def colleague_page_rated(self, colleague_id, head_id):
        
        employee_info = self.db.get_id_userinfo(colleague_id)
        userinfo = self.db.get_id_userinfo(colleague_id)
        print_info_first = enumerate(self.db.get_marks_rated_colleagues(employee_info['employee_record_card'],'first'))
        print_info_second = enumerate(self.db.get_marks_rated_colleagues(employee_info['employee_record_card'],'second'))

        return render_template('dashboard/colleague_page_rated.html', 
                                print_info_first=print_info_first,
                                print_info_second=print_info_second,
                                userinfo=userinfo,
                                colleague_id=colleague_id,
                                head_id=head_id
                                )
        
    def dashboard_admin(self):
        username= 'admin'
        password = 'admin'
        colleagues = self.db.get_colleagues(password,1)
        return render_template('admin/dashboard_admin.html', username=username, colleagues_list=colleagues)
    
    def logout(self):
        logout_user()
        return redirect(url_for('home'))

