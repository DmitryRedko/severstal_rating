import psycopg2

class DataBase:
    def __init__(self, db_settings):
        self.conn = psycopg2.connect(
            host=db_settings['host'],
            user=db_settings['user'],
            password=db_settings['password'],
            database=db_settings['dbname']
        )
        self.conn.autocommit = True
    
    def get_colleagues(self, head_record_card):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT employee_record_card, employee_full_name, department_position, department,  head_record_card, id
                    FROM staff
                    WHERE head_record_card = %s
                    """,
                    (head_record_card,)
                )
                result = cursor.fetchall()
        except:
            result = False
        return result
    
    
    def get_colleagues_rated(self, head_record_card):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT s.employee_record_card, s.employee_full_name, s.department_position, s.department,  s.head_record_card, s.id
                    FROM public.staff s
                    FULL JOIN public.rate_status rs ON s.id = rs.employee_id
                    WHERE rs.rate_status = true
                    AND s.head_record_card = %s;
                    """,
                    (head_record_card,)
                )
                result = cursor.fetchall()
        except:
            result = False
        return result
    
    
    def get_colleagues_to_rate(self, head_record_card):
        result = ''
        # try:
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT s.employee_record_card, s.employee_full_name, s.department_position, s.department,  s.head_record_card, s.id
                FROM public.staff s
                FULL JOIN public.rate_status rs ON s.id = rs.employee_id
                WHERE (rs.rate_status = false OR rs.rate_status IS NULL)
                AND s.head_record_card = %s;
                """,
                (head_record_card,)
            )
            result = cursor.fetchall()
        # except:
        #     result = False
        return result
    
    def get_marks_rated_colleagues(self, employee_record_card, name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT employee_record_card, criterion, description, performance_date, min_score, max_score, performance, comment
                    FROM estimation_{name}
                    WHERE employee_record_card = %s
                    AND performance_date = (
                    SELECT MAX(performance_date)
                    FROM estimation_{name}
                    WHERE employee_record_card = %s
                    );
                    """,
                    (employee_record_card, employee_record_card,)
                )
                result = cursor.fetchall()
        except:
            result = False
        return result
    
    
    def get_auterisation_info(self):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT head_record_card, head_password, can_be_changed
                    FROM authentication
                    """
                    )
                result = cursor.fetchall()
        except:
            result = False
            
        return result
    
    def get_id_userinfo(self, number):
        infodict = {}
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT employee_full_name, department_position, department, employee_record_card, head_record_card, id
                    FROM staff
                    WHERE id = %s
                    """,
                    (number,)
                )
                result = cursor.fetchall()
                if not result:
                    return False
                else:
                    infodict = {
                        'full_name': result[0][0],
                        'department': result[0][2],
                        'department_position': result[0][1],
                        'employee_record_card': result[0][3],
                        'head_record_card': result[0][4],
                        'user_id': result[0][5]
                    }
        except:
            result = "Ошибка обращения к базе данных"
            infodict = False
        return infodict
    
    def get_num_record_userinfo(self, number):
        infodict = {}
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT employee_full_name, department_position, department, employee_record_card, head_record_card, id
                    FROM staff
                    WHERE employee_record_card = %s
                    """,
                    (number,)
                )
                result = cursor.fetchall()
                if not result:
                    return False
                else:
                    infodict = {
                        'full_name': result[0][0],
                        'department': result[0][2],
                        'department_position': result[0][1],
                        'employee_record_card': result[0][3],
                        'head_record_card': result[0][4],
                        'user_id': result[0][5]
                    }
        except:
            result = "Ошибка обращения к базе данных"
            infodict = False
        return infodict
    
    def add_mark_to_base(self, dictmark, name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                for i in range(len(dictmark)):
                    cursor.execute(
                        f"""
                        INSERT INTO estimation_{name} (employee_record_card, criterion, description, performance_date, min_score, max_score, performance, comment)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (dictmark[i][0],dictmark[i][1],dictmark[i][2],dictmark[i][3],dictmark[i][4],dictmark[i][5],dictmark[i][6],dictmark[i][7],)
                        )
            result = True
        except:
            result = False
        return result

    def get_criterias_name_named_block(self, staff_id,name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT c.criterion, c.description, c.min_score, c.max_score
                    FROM staff s
                    JOIN {name}_block c ON s.department = c.department
                                AND s.department_position = c.department_position
                    WHERE s.id = %s;""",
                    (staff_id,)
                )
                result = cursor.fetchall()
        except:
            result = "Ошибка обращения к базе данных"
        return result

    def update_rating_status(self, colleague_id,head_id,status):
        print("HERE")
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO rate_status (head_id, employee_id, rate_status)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (head_id, employee_id)
                    DO UPDATE SET rate_status = %s;
                    """,
                    (head_id,colleague_id,bool(status),bool(status))
                )
        except:
            result = "Ошибка обращения к базе данных"
        return result
    
    def get_rating_status(self, colleague_id,head_id):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT rate_status
                FROM rate_status
                WHERE head_id = %s
                AND employee_id = %s;
                """,
                (head_id,colleague_id,)
            )
            result = cursor.fetchall()
        return result != []
    
    def set_new_password(self, head_id, new_password):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE authentication
                    SET head_password = %s
                    WHERE head_record_card = %s;
                    """,
                    (new_password, head_id,)
                )
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE authentication
                    SET can_be_changed = false
                    WHERE head_record_card = %s;
                    """,
                    (head_id,)
                )
        except:
            result = "Ошибка обращения к базе данных"
        return result
    
    def get_auterisation_info_by_record_card(self,head_record_card):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT head_record_card, head_password, can_be_changed
                    FROM authentication
                    WHERE head_record_card = %s
                    """,
                    (head_record_card,)
                    )
                result = cursor.fetchall()
        except:
            result = False
        return result
    