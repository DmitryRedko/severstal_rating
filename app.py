from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from user import UserManager, AdminManager, UserLogin
from config import dictionary, db_settings
from database import DataBase
import pandas as pd
from werkzeug.security import generate_password_hash
from datetime import datetime as dt
import datetime
import random
import string

class FlaskApp():
    def __init__(self):
        self.created_df = None
        self.__admin_criteria_flag = None
        self.__admin_filter_flag = None
        self.__first_filtred_criterias = []
        self.__second_filtred_criterias = []
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
        self.app.route('/create_report',methods=['GET','POST'])(self.create_report)
        self.app.route('/admin_rate_access',methods=['GET','POST'])(self.admin_rate_access)
        self.app.route('/page_access_colleague_page/<string:colleague_id>/<string:head_id>',methods=['GET','POST'])(self.page_access_colleague_page)
        self.app.route('/admin_menu_change_password',methods=['GET','POST'])(self.admin_menu_change_password)
        self.app.route('/admin_criteria', methods=['GET','POST'])(self.admin_criteria)
        self.app.route('/change_criteria/<string:criteria_id>/<int:bool_block_status>', methods=['GET','POST'])(self.change_criteria)  
        self.app.route('/add_criteria', methods=['GET','POST'])(self.add_criteria)      
        self.app.route('/user_base', methods=['GET','POST'])(self.user_base)      
        self.app.route('/change_user/<string:user_id>', methods=['GET','POST'])(self.change_user)
        self.app.route('/add_user', methods=['GET','POST'])(self.add_user)      
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
            if self.admin_manager.login_admin(username, password):
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

    @login_required
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
            flag = 0
            try:
                flag = self.db.get_current_rate_status(colleague_id, head_id)[0][0]
            except:
                flag = False
            if (status_first == 1 and status_second == 1 and flag == False):
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
                password_hashed = generate_password_hash(password_new)
                self.db.set_new_password(
                    userinfo['employee_record_card'], password_hashed)
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
    
    @login_required
    def __init_report_df(self):
        max_scores = pd.DataFrame(self.db.get_max_scores(), columns=['head_department', 'department', 'department_position', 'final_total_max_score'])
        marks = pd.DataFrame(self.db.get_staff_marks(), columns=['employee_record_card', 'performance_date', 'final_total_performance'])
        info = pd.DataFrame([self.db.get_num_record_userinfo(row) for row in list(marks['employee_record_card'])])
        headinfo = pd.DataFrame([self.db.get_num_record_userinfo(row) for row in list(info['head_record_card'])])
        headinfo = (headinfo[['full_name', 'employee_record_card']]).rename(columns={'full_name': 'head_name','employee_record_card': 'head_record_card'})
    
        merged_table = pd.merge(info, marks, on='employee_record_card', how='right')
        merged_table = pd.merge(merged_table, max_scores, on=['head_department', 'department', 'department_position'], how='left')
        merged_table = pd.merge(merged_table, headinfo, on='head_record_card',  how='inner')
        
        self.created_df = merged_table.drop_duplicates()
        
        # print()
        # print(max_scores)
        # print()
        # print(marks)
        # print()
        # print(info)
        # print()
        # print(headinfo)
        
    # Сделаю попозже
    # def __create_statistic_plot(self):
    #     labels = ['Еще не проголосовали', 'Проголосовали', ]
    #     sizes = [len(self.created_df), 40]
    #     colors = ['red', 'green']

    #     plt.figure()
    #     plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
    #     plt.axis('equal')  


    #     # Сохраняем график в буфер
    #     buffer = io.BytesIO()
    #     plt.savefig(buffer, format='png')
    #     buffer.seek(0)

    #     # Преобразуем график в формат base64 для передачи в HTML
    #     plot_data = base64.b64encode(buffer.getvalue()).decode()

    #     buffer.close()
        
    #     return plot_data

    @login_required
    def dashboard_admin(self):
        try:
            self.__init_report_df()
        except Exception:
            pass 
        return render_template('admin/dashboard_admin.html')

    @login_required
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
    @login_required
    def head_statistic(self, head_id):
        head_info = self.db.get_id_userinfo(head_id)
        colleagues = self.db.get_colleagues(head_info['employee_record_card'])
        head_username, head_id = head_info['full_name'], head_info['user_id']
        return render_template('admin/rate_statistic/head_statistic.html',
                               username=head_username,
                               colleagues_list=colleagues,
                               head_id=head_id,
                               )
    @login_required
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
    
    @login_required  
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
    
    @login_required
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
    @login_required  
    def create_report(self):
        flag = 0
        try:
            self.__init_report_df()
        except Exception:
            flag = 1
        
        head_department_list = self.db.get_head_departments_list()
        head_department_enumerated = list(enumerate(head_department_list))
        try:
            if(flag == 1):
                raise ValueError
            coefficient = round(self.created_df['final_total_max_score'].max(), 2)
        except:
            coefficient = "Не может быть вычислен"
            
        if('report' in request.form):
            writer = pd.ExcelWriter('Report.xlsx', engine="openpyxl")
            filtred_head_department=''
            start_date_str = request.form['start_date']
            end_date_str = request.form['end_date']
            self.report_name = request.form.get('report_name')
            if(self.report_name is None or self.report_name== ''):
                self.report_name = 'Performance_report'
            start_date=''
            end_date=''
            if(start_date_str is None or end_date_str is None or start_date_str == '' or end_date_str == ''):
                flash('Списокуток времени не задан.', category='error')
                flag = 1
            else:
                start_date = dt.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = dt.strptime(end_date_str, "%Y-%m-%d").date()
            head_department_on = []
            for index, department in head_department_enumerated:
                head_department_on.append(department) if request.form.get(str(index)) == 'on' else None
            
            if(len(head_department_on) == 0):
                flash('Укажите отделы, для которых нужно сформировать отчет.', category='error')
                flag = 1
            
            if(flag == 0 and self.created_df is not None):
                for head_department in head_department_on:
                    filtred_head_department = (self.created_df[self.created_df['head_department'] == head_department])
                    filtred_head_department = filtred_head_department.loc[(filtred_head_department['performance_date'] < end_date) & (filtred_head_department['performance_date'] >= start_date)]
                    filtred_head_department['final_total_performance'] = filtred_head_department['final_total_performance']/filtred_head_department['final_total_max_score']*coefficient
                    print(filtred_head_department.columns)
                    filtred_head_department['comment'] = None
                    excel_df = filtred_head_department[['department','full_name','department_position', 'final_total_performance','comment','head_name']]
                    new_headers = {
                        'department': 'Отдел',
                        'full_name': 'Полное имя',
                        'department_position': 'Должность',
                        'final_total_performance': 'Итоговая производительность',
                        'comment': 'Комментарий',
                        'head_name': 'Имя руководителя'
                    }
                    excel_df = excel_df.rename(columns=new_headers)
                    excel_df.to_excel(writer, sheet_name=head_department, index=False)
                workbook = writer.book
                sheets = workbook.sheetnames
                
                for sheet_name in sheets:
                    sheet = workbook[sheet_name]
                    for column_cells in sheet.columns:
                        max_length = 0
                        for cell in column_cells:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(cell.value)
                            except:
                                pass
                        adjusted_width = (max_length + 2) * 1.2
                        sheet.column_dimensions[cell.column_letter].width = adjusted_width

                # Сохранение документа Excel
                workbook.save('Report.xlsx')
            
        return render_template('admin/create_report/create_report.html', coefficient=coefficient, head_department_enumerated=head_department_enumerated)
    
    @login_required
    def admin_rate_access(self):
        if request.method == 'POST' and 'del_rate' in request.form:
            user_id_del = request.form.get('user_id_del')
            head_id_del = request.form.get('head_id_del')
            user_num_del = str((self.db.get_id_userinfo(user_id_del))['employee_record_card'])
            print(user_num_del)
            flag_first = self.db.del_last_rate(user_num_del,'first')
            flag_second = self.db.del_last_rate(user_num_del,'second')
            if(flag_first and flag_second):
                self.db.update_rating_status(user_id_del, head_id_del, 0)
            print(flag_first, flag_second)
            
            
        if request.method == 'POST' and 'del_all' in request.form:
            self.db.del_all_performances()
        if request.method == 'POST' and 'reset_all' in request.form:
            self.db.reset_all_statuses()
        rate_list = []
        all_rate_statuses = self.db.get_all_rate_statuses()
        print(all_rate_statuses)
        for i in range(len(all_rate_statuses)):
            print(all_rate_statuses[i])
            headname = self.db.get_id_userinfo(all_rate_statuses[i][0])['full_name']
            username = self.db.get_id_userinfo(all_rate_statuses[i][1])['full_name']
            rate_list.append(
                {'head_id': all_rate_statuses[i][0],
                 'user_id': all_rate_statuses[i][1],
                 'headname': headname,
                 'username' : username
                 })
        return render_template('admin/rate_access/rate_access.html', rate_list = rate_list)
    
    @login_required
    def page_access_colleague_page(self, colleague_id, head_id):
        employee_info = self.db.get_id_userinfo(colleague_id)
        userinfo = self.db.get_id_userinfo(colleague_id)
        print_info_first = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'first'))
        print_info_second = enumerate(
            self.db.get_marks_rated_colleagues(
                employee_info['employee_record_card'], 'second'))

        return render_template('admin/rate_access/page_access_colleague_page.html',
                               print_info_first=print_info_first,
                               print_info_second=print_info_second,
                               userinfo=userinfo,
                               colleague_id=colleague_id,
                               head_id=head_id
                               )

    @login_required
    def __generate_random_password(self,length=2):
        special_characters = '!@#$%^&*()_+=<>?'
        characters = string.ascii_letters + string.digits + special_characters
        password = ''.join(random.choice(characters) for i in range(length))
        return password

    @login_required
    def admin_menu_change_password(self):
        password = ''
        head_id_current = ''
        if request.method == 'POST' and 'password_change' in request.form:
            head_id_current = request.form.get('head_id')
            password = self.__generate_random_password()
            hashed_password = generate_password_hash(password)
            print(password)
            print(hashed_password)
            self.db.set_new_password_admin(head_id_current, hashed_password)
            
        auterisation_info = self.db.get_auterisation_info() 
        print_info = []
        for row in auterisation_info:
            userinfo = self.db.get_id_userinfo(row[0])
            print_info.append([row[0], userinfo['full_name']])
            
        return render_template('admin/change_password/change_password.html',
                               head_id_current = head_id_current,
                               print_info = print_info,
                               password = password
                               )

    @login_required
    def admin_criteria(self):
        print(request.form)
        
        if self.__admin_criteria_flag is None:
            self.__admin_criteria_flag = 0
            
            
        if request.method == 'POST' and "filter" in request.form:
            self.head_department_criteria = request.form.get('head_department')
            self.department_criteria = request.form.get('department')
            self.department_position_criteria = request.form.get('department_position')
            if(self.head_department_criteria!='' and self.department_criteria!='' and self.department_position_criteria!='' and self.head_department_criteria!=None and self.department_position_criteria!=None and self.department_position_criteria!=None):
                self.__first_filtred_criterias = self.db.get_named_criterias(self.head_department_criteria, self.department_criteria, self.department_position_criteria,'first')
                self.__second_filtred_criterias = self.db.get_named_criterias(self.head_department_criteria, self.department_criteria, self.department_position_criteria,'second')
                if(len(self.__second_filtred_criterias)>0 or len(self.__first_filtred_criterias)>0):
                    self.__admin_criteria_flag = 1
                else:
                    flash("Ничего не найдено", category='error')        
            else:
                flash("Нужно заполнить все поля", category='error')   
                 
        if request.method == 'POST' and 'filter_menu' in request.form:
            self.__admin_criteria_flag = 0

        if request.method == 'POST' and 'delete' in request.form:
            first_criteria_id = request.form.get('first_criteria_id')
            second_criteria_id = request.form.get('second_criteria_id')
            if (first_criteria_id is not None):
                self.db.delete_criteria_by_id(first_criteria_id, 'first')
            elif (second_criteria_id is not None):
                self.db.delete_criteria_by_id(second_criteria_id, 'second')
            self.__first_filtred_criterias = self.db.get_named_criterias(self.head_department_criteria, self.department_criteria, self.department_position_criteria,'first')
            self.__second_filtred_criterias = self.db.get_named_criterias(self.head_department_criteria, self.department_criteria, self.department_position_criteria,'second')
               
        if request.method == 'POST' and 'update' in request.form:
            first_criteria_id = request.form.get('first_criteria_id')
            second_criteria_id = request.form.get('second_criteria_id')
            if (first_criteria_id is not None):
                return redirect(url_for('change_criteria', criteria_id = first_criteria_id, bool_block_status = False))
            elif (second_criteria_id is not None):
                return redirect(url_for('change_criteria', criteria_id = second_criteria_id, bool_block_status = True))
        
        if request.method == 'POST' and 'add' in request.form:
            return redirect(url_for('add_criteria'))
        
        
            
        return render_template('admin/admin_criteria/admin_criteria.html',
                               status_print = self.__admin_criteria_flag,
                               first_criterias = self.__first_filtred_criterias,
                               second_criterias = self.__second_filtred_criterias)
    
    @login_required
    def change_criteria(self, criteria_id,bool_block_status):
        name = 'second' if bool_block_status else 'first'
        if request.method == 'POST':
            criteria = request.form.get('criteria')
            description = request.form.get('description')
            min_score = request.form.get('min_score')
            max_score = request.form.get('max_score')
            self.db.update_criteria_by_id(criteria, description, min_score, max_score, criteria_id, name)
        info = self.db.get_criteria_by_id(criteria_id,name)[0]
        infodict = {
            'criteria_id':info[0],
            'head_department':info[1],
            'department':info[2],
            'department_position':info[3],
            'criteria':info[4],
            'description':info[5],
            'min':info[6],
            'max':info[7],
        }
        return render_template('admin/admin_criteria/change_criteria.html', bool_block_status = bool_block_status, info = infodict)
    
    @login_required
    def add_criteria(self):
        if request.method == 'POST' and 'add' in request.form:
            block = request.form.get('block')
            head_department = request.form.get('head_department')
            department = request.form.get('department')
            department_position = request.form.get('department_position')
            criteria = request.form.get('criteria')
            description = request.form.get('description')
            min_score = request.form.get('min_score')
            max_score = request.form.get('max_score')
            print(block, head_department, department, department_position, criteria, description, min_score, max_score)
            if head_department !='' and department!='' and department_position!='' and criteria!='' and description!='' and min_score!='' and max_score!='':
                status = self.db.add_criteria(block, head_department, department, department_position, criteria, description, min_score, max_score)
                if(status != False):
                    flash("Критерий успешно добавлен")
                else:
                    flash("Ошибка добавления в базу")
            else:
                flash("Не все поля заполнены")
        return render_template('admin/admin_criteria/add_criteria.html')
       
    @login_required 
    def user_base(self):
        print(request.form)
        info_dict = {}
        if self.__admin_filter_flag is None:
            self.__admin_filter_flag = 0

        if request.method == 'POST' and "filter" in request.form:
            head_department = request.form.get('head_department')
            department = request.form.get('department')
            department_position = request.form.get('department_position')
            full_name = request.form.get('full_name')
            employee_record_card = request.form.get('employee_record_card')
            head_record_card = request.form.get('head_record_card')
            info_dict = {
            'head_department':head_department,
            'department':department,
            'department_position':department_position,
            'employee_full_name':full_name,
            'employee_record_card':employee_record_card,
            'head_record_card':head_record_card
            }
            self.__admin_filter_flag = 0
            
        users = self.db.get_users_base(info_dict)
                 
        if request.method == 'POST' and 'filter_menu' in request.form:
            self.__admin_filter_flag = 1

        if request.method == 'POST' and 'delete' in request.form:
            user = request.form.get('user_record_card')
            self.db.delete_user_by_record_card(user)
               
        if request.method == 'POST' and 'update' in request.form:
            user = request.form.get('user_record_card')
            return redirect(url_for('change_user', user_id = self.db.get_num_record_userinfo(user)['user_id']))
        
        if request.method == 'POST' and 'add' in request.form:
            return redirect(url_for('add_user'))
        
            
        return render_template('admin/users_base/user_base.html',
                               filter_flag = self.__admin_filter_flag,
                               users = users
                               )
        
    @login_required
    def change_user(self, user_id):
        if request.method == 'POST':
            head_department = request.form.get('head_department')
            department = request.form.get('department')
            department_position = request.form.get('department_position')
            full_name = request.form.get('full_name')
            employee_record_card = request.form.get('employee_record_card')
            head_record_card = request.form.get('head_record_card')
            self.db.update_user_by_id(user_id, head_department, department, department_position, full_name, employee_record_card, head_record_card)
            
        infodict = self.db.get_id_userinfo(user_id)
        print(infodict)
        return render_template('admin/users_base/change_user.html', info = infodict)
    
    @login_required
    def add_user(self):
        if request.method == 'POST' and 'add' in request.form:
            head_department = request.form.get('head_department')
            department = request.form.get('department')
            department_position = request.form.get('department_position')
            full_name = request.form.get('full_name')
            employee_record_card = request.form.get('employee_record_card')
            head_record_card = request.form.get('head_record_card')
            
            if head_department !='' and department!='' and department_position!='' and full_name!='' and employee_record_card!='' and head_record_card!='':
                status = self.db.add_user(head_department, department, department_position, full_name, employee_record_card, head_record_card)
                if(status != False):
                    flash("Сотрудник успешно добавлен")
                else:
                    flash("Ошибка добавления в базу")
            else:
                flash("Не все поля заполнены")
        return render_template('admin/users_base/add_user.html')