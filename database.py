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
        except BaseException:
            result = False
        return result

    def get_colleagues_rated(self, head_record_card):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT s.employee_record_card, s.employee_full_name, s.department_position, s.department,  s.head_record_card, s.id
                    FROM staff s
                    FULL JOIN rate_status rs ON s.id = rs.employee_id
                    WHERE rs.rate_status = true
                    AND s.head_record_card = %s;
                    """,
                    (head_record_card,)
                )
                result = cursor.fetchall()
        except BaseException:
            result = False
        return result

    def get_colleagues_to_rate(self, head_record_card):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT s.employee_record_card, s.employee_full_name, s.department_position, s.department,  s.head_record_card, s.id
                    FROM staff s
                    FULL JOIN rate_status rs ON s.id = rs.employee_id
                    WHERE (rs.rate_status = false OR rs.rate_status IS NULL)
                    AND s.head_record_card = %s;
                    """,
                    (head_record_card,)
                )
                result = cursor.fetchall()
        except:
            result = False
        return result

    def get_marks_rated_colleagues(self, employee_record_card, name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT employee_record_card, criteria, description, performance_date, min_score, max_score, performance, comment
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
        except BaseException:
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
        except BaseException:
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
        except BaseException:
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
                    SELECT employee_full_name, department_position, department,  employee_record_card, head_record_card, id, head_department
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
                        'user_id': result[0][5],
                        'head_department': result[0][6]
                    }
        except BaseException:
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
                        INSERT INTO estimation_{name} (employee_record_card, criteria, description, performance_date, min_score, max_score, performance, comment)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (dictmark[i][0],
                         dictmark[i][1],
                            dictmark[i][2],
                            dictmark[i][3],
                            dictmark[i][4],
                            dictmark[i][5],
                            dictmark[i][6],
                            dictmark[i][7],
                         ))
            result = True
        except BaseException:
            result = False
        return result

    def get_criterias_name_named_block(self, staff_id, name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT c.criteria, c.description, c.min_score, c.max_score
                    FROM staff s
                    JOIN {name}_block c ON s.department = c.department
                                AND s.department_position = c.department_position
                    WHERE s.id = %s;""",
                    (staff_id,)
                )
                result = cursor.fetchall()
        except BaseException:
            result = "Ошибка обращения к базе данных"
        return result

    def update_rating_status(self, colleague_id, head_id, status):
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
                    (head_id, colleague_id, bool(status), bool(status))
                )
        except BaseException:
            result = "Ошибка обращения к базе данных"
        return result

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
        except BaseException:
            result = "Ошибка обращения к базе данных"
        return result

    def get_auterisation_info_by_record_card(self, head_record_card):
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
        except BaseException:
            result = False
        return result

    def get_head_departments_list(self):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT DISTINCT head_department FROM staff;
                    """
                )
                result = cursor.fetchall()
                result_list = []
                for row in result:
                    result_list.append(row[0])
                result = result_list
        except BaseException:
            result = False
        return result
    
    def get_max_scores(self):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT t1.head_department, t1.department, t1.department_position,
                        t1.total_max_score * COALESCE(t2.total_max_score, 1) AS final_total_max_score
                    FROM (
                        SELECT head_department, department, department_position,
                            EXP(SUM(LN(max_score))) AS total_max_score
                        FROM first_block
                        GROUP BY head_department, department, department_position
                    ) AS t1
                    LEFT JOIN (
                        SELECT head_department, department, department_position,
                            SUM(max_score) AS total_max_score
                        FROM second_block
                        GROUP BY head_department, department, department_position
                    ) AS t2
                    ON t1.head_department = t2.head_department
                    AND t1.department = t2.department
                    AND t1.department_position = t2.department_position;
                    """
                )
                result = cursor.fetchall()
        except BaseException:
            result = False
        return result

    def get_staff_marks(self):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT t1.employee_record_card, 
                        t1.performance_date, 
                        t1.total_performance * COALESCE(t2.total_performance, 1) AS final_total_performance
                    FROM (
                        SELECT employee_record_card, 
                            performance_date, 
                            EXP(SUM(LN(performance))) AS total_performance
                        FROM estimation_first
                        GROUP BY employee_record_card, performance_date
                    ) AS t1
                    LEFT JOIN (
                        SELECT employee_record_card, 
                            performance_date, 
                            SUM(performance) AS total_performance
                        FROM estimation_second
                        GROUP BY employee_record_card, performance_date
                    ) AS t2 ON t1.employee_record_card = t2.employee_record_card
                        AND t1.performance_date = t2.performance_date;
                    """
                )
                result = cursor.fetchall()
        except BaseException:
            result = False
        return result
    
    def get_all_rate_statuses(self):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT head_id, employee_id, rate_status
                    FROM rate_status
                    WHERE rate_status = 'true';
                    """
                )
                result = cursor.fetchall()
        except BaseException:
            result = False
        return result
    
    def get_current_rate_status(self, colleague_id, head_id):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT rate_status
                FROM rate_status
                WHERE head_id = %s
                AND employee_id = %s;
                """,
                (head_id, colleague_id,)
            )
            result = cursor.fetchall()
        return result
    
    def get_current_rate_status(self, colleague_id, head_id):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT rate_status
                FROM rate_status
                WHERE head_id = %s
                AND employee_id = %s;
                """,
                (head_id, colleague_id,)
            )
            result = cursor.fetchall()
        return result
    
    def del_last_rate(self, colleague_record_card, name):
        result_status = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    DELETE FROM estimation_{name}
                    WHERE (employee_record_card, performance_date) IN (
                        SELECT employee_record_card, MAX(performance_date)
                        FROM estimation_{name}
                        WHERE employee_record_card = %s
                        GROUP BY employee_record_card
                    );
                    """,
                    (colleague_record_card,)
                )
                result_status = True
        except BaseException:
            result_status = False
        return result_status

    def del_all_performances(self):
        with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM estimation_first;")
        with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM estimation_second;")
        with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM rate_status;")

    def reset_all_statuses(self):
        with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM rate_status;")
    
    def set_new_password_admin(self, head_id, new_password):
        result = ''
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
                    SET can_be_changed = true
                    WHERE head_record_card = %s;
                    """,
                    (head_id,)
                )
                
    def get_named_criterias(self,head_department, department, department_position,name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, head_department, department, department_position, criteria, description, min_score, max_score
                    FROM {name}_block
                    WHERE head_department = %s AND department = %s AND department_position = %s;
                    """,
                    (head_department, department, department_position, )
                )
                result = cursor.fetchall()
        except BaseException:
            result = False
        return result
    
    def get_criteria_by_id(self,criteria_id,name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT id, head_department, department, department_position, criteria, description, min_score, max_score
                    FROM {name}_block
                    WHERE id = %s;
                    """,
                    (criteria_id,)
                )
                result = cursor.fetchall()
        except BaseException:
            result = False
        return result   
    
    def update_criteria_by_id(self,criteria, description, min_score, max_score, criteria_id,name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE {name}_block
                    SET criteria = %s,
                    description = %s,
                    min_score = %s,
                    max_score = %s
                    WHERE id = %s;
                    """,
                    (criteria, description, min_score, max_score, criteria_id,)
                )
            result = cursor.fetchall()
        except BaseException:
            result = False
        return result
    
    def delete_criteria_by_id(self,criteria_id,name):
        result = ''
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    DELETE FROM {name}_block
                    WHERE id = %s
                    """,
                    (criteria_id,)
                )
                result = cursor.fetchall()
        except BaseException:
            result = False
        return result