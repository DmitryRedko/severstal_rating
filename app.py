from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from functools import wraps
from user import UserManager, AdminManager, UserLogin
from config import dictionary, db_settings
from database import DataBase
from werkzeug.security import generate_password_hash, check_password_hash
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
        self.app.route('/dashboard_admin',methods=['GET','POST'])(self.dashboard_admin)
        self.app.route('/dashboard/<string:head_id>',methods=['GET','POST'])(self.dashboard)
        self.app.route('/change_password/<string:head_id>',methods=['GET','POST'])(self.change_password)
        self.app.route('/dashboard_rated/<string:head_id>',methods=['GET','POST'])(self.dashboard_rated)
        self.app.route('/dashboard_to_rate/<string:head_id>',methods=['GET','POST'])(self.dashboard_to_rate)
        self.app.route('/colleague_page/<string:colleague_id>/<string:head_id>', methods=['GET','POST'])(self.colleague_page)
        self.app.route('/colleague_page_rated/<string:colleague_id>/<string:head_id>',methods=['GET','POST'])(self.colleague_page_rated)
        self.app.route('/dashboard_main_heads',methods=['GET','POST'])(self.dashboard_main_heads)
        self.app.route('/head_statistic/<string:head_id>',methods=['GET','POST'])(self.head_statistic)
        self.app.route('/head_statistic_rated/<string:head_id>',methods=['GET','POST'])(self.head_statistic_rated)
        self.app.route('/head_statistic_to_rate/<string:head_id>',methods=['GET','POST'])(self.head_statistic_to_rate)
        self.app.route('/head_colleague_page_rated/<string:colleague_id>/<string:head_id>',methods=['GET','POST'])(self.head_colleague_page_rated)
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
                user_id = self.db.get_num_record_userinfo(username)['user_id']
                user_login = UserLogin().create(user_id)
                login_user(user_login)
                session['username'] = username
                session['password'] = password
                return redirect(url_for('dashboard', head_id=user_id))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('dashboard/login.html', error=error)
        return render_template('dashboard/login.html')

    def load_user(self, user_id):
        return UserLogin().get_user_from_DB(user_id, self.db)

    def admin(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if self.admin_manager.verify_admin(username, password):
                session['username'] = username
                return redirect(url_for('dashboard_admin'))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('admin/admin.html', error=error)
        return render_template('admin/admin.html')

    @login_required
    def dashboard(self, head_id):
        head_info = self.db.get_id_userinfo(head_id)
        check_password_status = self.db.get_auterisation_info_by_record_card(
            head_info['employee_record_card'])[0][2]
        colleagues = self.db.get_colleagues(head_info['employee_record_card'])
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template(
            'dashboard/dashboard.html',
            username=head_username,
            colleagues_list=colleagues,
            head_id=head_id,
            check_password_status=check_password_status)

    @login_required
    def dashboard_rated(self, head_id):
        head_info = self.db.get_id_userinfo(head_id)
        colleagues = self.db.get_colleagues_rated(
            head_info['employee_record_card'])
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template(
            'dashboard/dashboard_rated.html',
            username=head_username,
            colleagues_list=colleagues,
            head_id=head_id)

    @login_required
    def dashboard_to_rate(self, head_id):
        head_info = self.db.get_id_userinfo(head_id)
        colleagues = self.db.get_colleagues_to_rate(
            head_info['employee_record_card'])
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template(
            'dashboard/dashboard_to_rate.html',
            username=head_username,
            colleagues_list=colleagues,
            head_id=head_id)

    def __get_mark_list(self, colleague_num, name, userinfo, date):
        criterias = self.db.get_criterias_name_named_block(colleague_num, name)
        criterias_list, min_score, max_score, description = [], [], [], []
        for row in criterias:
            criterias_list.append(row[0])
            description.append(row[1])
            min_score.append(row[2])
            max_score.append(row[3])
        mark_msgs = []
        marks = []
        flag = 0
        status = 0
        for i in range(len(criterias_list)):
            mark = 0
            if (name == 'first'):
                mark = request.form.get(f"markf_{i}")
                mark_msgs.append(request.form.get(f"messf_{i}"))
            else:
                mark = request.form.get(f"marks_{i}")
                mark_msgs.append(request.form.get(f"messs_{i}"))

            if (mark != '' and mark is not None):
                marks.append(float(mark))
            else:
                flag = 1
                break
        if (len(marks) == len(criterias_list) and flag == 0):
            status = 1
        listmark = []
        if (flag == 0 and status == 1):
            for i in range(len(criterias_list)):
                listmark.append([userinfo['employee_record_card'],
                                 criterias_list[i],
                                 description[i],
                                 date,
                                 min_score[i],
                                 max_score[i],
                                 marks[i],
                                 mark_msgs[i]])
        return listmark, status

    @login_required
    def colleague_page(self, colleague_id, head_id):
        listmark_first, listmark_second, status = [], [], 0
        status_msg = ''
        userinfo = self.db.get_id_userinfo(colleague_id)
        date = datetime.date.today().strftime("%d.%m.%Y")
        if request.method == 'POST' and "submit_button" in request.form:
            listmark_first, status_first = self.__get_mark_list(
                colleague_id, 'first', userinfo, date)
            listmark_second, status_second = self.__get_mark_list(
                colleague_id, 'second', userinfo, date)
            if (status_first == 1 and status_second ==
                    1 and self.db.get_rating_status(colleague_id, head_id) == 0):
                status1 = self.db.add_mark_to_base(listmark_first, 'first')
                status2 = self.db.add_mark_to_base(listmark_second, 'second')
                if (status1 and status2):
                    flash('Результаты успешно сохранены.', category='success')
                else:
                    flash('Ошибка добавления данных в базу.', category='error')
                self.db.update_rating_status(colleague_id, head_id, 1)
                status = 1
            elif (status_first == 0 or status_second == 0):
                flash(
                    'Пожалуйста, заполните все доступные критери.',
                    category='error')
            else:
                flash('Вы уже оценили данного сотрудника.', category='error')

        info_first = self.db.get_criterias_name_named_block(
            colleague_id, 'first')
        info_second = self.db.get_criterias_name_named_block(
            colleague_id, 'second')
        print_info_first = enumerate(
            [[row[0], row[1], date, row[2], row[3]] for row in info_first])
        print_info_second = enumerate(
            [[row[0], row[1], date, row[2], row[3]] for row in info_second])

        return render_template('dashboard/colleague_page.html',
                               print_info_first=print_info_first,
                               print_info_second=print_info_second,
                               userinfo=userinfo,
                               date=date,
                               status_msg=status_msg,
                               status=status,
                               colleague_id=colleague_id,
                               head_id=head_id
                               )

    @login_required
    def colleague_page_rated(self, colleague_id, head_id):

        employee_info = self.db.get_id_userinfo(colleague_id)
        userinfo = self.db.get_id_userinfo(colleague_id)
        print_info_first = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'first'))
        print_info_second = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'second'))

        return render_template('dashboard/colleague_page_rated.html',
                               print_info_first=print_info_first,
                               print_info_second=print_info_second,
                               userinfo=userinfo,
                               colleague_id=colleague_id,
                               head_id=head_id
                               )

    @login_required
    def change_password(self, head_id):
        if request.method == 'POST':
            password_new = request.form['password_new']
            password_new_again = request.form['password_new_again']
            userinfo = self.db.get_id_userinfo(head_id)
            can_change_flag = self.db.get_auterisation_info_by_record_card(
                userinfo['employee_record_card'])[0][2]
            if (password_new_again == password_new and can_change_flag):
                self.db.set_new_password(
                    userinfo['employee_record_card'], password_new)
                flash('Пароль успешно изменен.', category='success')
            elif (password_new_again != password_new):
                flash('Пароли не совпадают.', category='error')
            else:
                flash('Вы не можете изменить пароль.', category='error')
        return render_template(
            'dashboard/change_password.html',
            head_id=head_id)

    def logout(self):
        logout_user()
        return redirect(url_for('home'))

    def dashboard_admin(self):
        return render_template('admin/dashboard_admin.html')

    def dashboard_main_heads(self):
        auterisation_info = self.db.get_auterisation_info()
        head_record_info, colleagues_reated, colleagues, color = [], [], [], []
        for row in auterisation_info:
            head_record_info.append(self.db.get_num_record_userinfo(row[0]))
            colleagues_reated.append(len(self.db.get_colleagues_rated(row[0])))
            colleagues.append(len(self.db.get_colleagues(row[0])))
            if (int((colleagues_reated[-1] / colleagues[-1]) * 100)) < 33:
                color.append('red')
            elif (int((colleagues_reated[-1] / colleagues[-1]) * 100)) < 66:
                color.append('orange')
            else:
                color.append('green')
        print(head_record_info)
        print(colleagues_reated)
        print(colleagues)
        print(color)

        print(head_record_info)

        return render_template('admin/rate_statistic/dashboard_main_heads.html',
                               head_record_nums=head_record_info,
                               colleagues=colleagues,
                               colleagues_reated=colleagues_reated,
                               color=color
                               )

    def head_statistic(self, head_id):
        head_info = self.db.get_id_userinfo(head_id)
        colleagues = self.db.get_colleagues(head_info['employee_record_card'])
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template('admin/rate_statistic/head_statistic.html',
                               username=head_username,
                               colleagues_list=colleagues,
                               head_id=head_id,
                               )
    
    def head_statistic_rated(self, head_id):
        head_info = self.db.get_id_userinfo(head_id)
        colleagues = self.db.get_colleagues_rated(
            head_info['employee_record_card'])
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template(
            'admin/rate_statistic/head_statistic_rated.html',
            username=head_username,
            colleagues_list=colleagues,
            head_id=head_id)
        
    def head_statistic_to_rate(self, head_id):
        head_info = self.db.get_id_userinfo(head_id)
        colleagues = self.db.get_colleagues_to_rate(
            head_info['employee_record_card'])
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template(
            'admin/rate_statistic/head_statistic_to_rate.html',
            username=head_username,
            colleagues_list=colleagues,
            head_id=head_id)
    
    def head_colleague_page_rated(self, colleague_id, head_id):
        employee_info = self.db.get_id_userinfo(colleague_id)
        userinfo = self.db.get_id_userinfo(colleague_id)
        print_info_first = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'first'))
        print_info_second = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'second'))

        return render_template('admin/rate_statistic/head_colleague_page_rated.html',
                               print_info_first=print_info_first,
                               print_info_second=print_info_second,
                               userinfo=userinfo,
                               colleague_id=colleague_id,
                               head_id=head_id
                               )
    
    def head_colleague_page_rated(self, colleague_id, head_id):
        employee_info = self.db.get_id_userinfo(colleague_id)
        userinfo = self.db.get_id_userinfo(colleague_id)
        print_info_first = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'first'))
        print_info_second = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'second'))

        return render_template('admin/rate_statistic/head_colleague_page_rated.html',
                               print_info_first=print_info_first,
                               print_info_second=print_info_second,
                               userinfo=userinfo,
                               colleague_id=colleague_id,
                               head_id=head_id
                               )
