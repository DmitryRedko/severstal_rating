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
    
    def get_colleagues(self, head_record_card, admin):
        result = ''
        if admin == 0:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM staff
                    WHERE head_record_card = %s
                    """,
                    (head_record_card,)
                )
                result = cursor.fetchall()
        else:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM staff
                    """
                )
                result = cursor.fetchall()
        return result
    
    def get_head_colleagues(self):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT employee_full_name, employee_record_card
                FROM staff
                WHERE employee_record_card IN (SELECT DISTINCT head_record_card FROM staff);
                """
                )
            result = cursor.fetchall()
        return dict(result)
    
    def get_num_record_userinfo(self, number):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT employee_full_name, department_position, department, employee_record_card, head_record_card
                FROM staff
                WHERE employee_record_card = %s
                """,
                (number,)
            )
            result = cursor.fetchall()
            print(result)
            infodict = {
                'full_name': result[0][0],
                'department': result[0][2],
                'department_position': result[0][1],
                'employee_record_card': result[0][3],
                'head_record_card': result[0][4]
            }
        return infodict
    
    def add_mark_to_base(self, dictmark, name):
        with self.conn.cursor() as cursor:
            for i in range(len(dictmark)):
                cursor.execute(
                    f"""
                    INSERT INTO estimation_{name} (employee_record_card, criterion, performance_date, performance, comment)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (dictmark[i][0],dictmark[i][1],dictmark[i][2],dictmark[i][3],dictmark[i][4])
                )

    def get_criterias_name_named_block(self, staff_num,name):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT c.criterion, c.description, c.min_score, c.max_score
                FROM staff s
                JOIN {name}_block c ON s.department = c.department
                            AND s.department_position = c.department_position
                WHERE s.employee_record_card = %s;""",
                (staff_num,)
            )
            result = cursor.fetchall()
        return result

    def update_rating_status(self, colleague_num,head_num,status):
        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                INSERT INTO rate_status (head_record_card, employee_record_card, rate_status)
                VALUES (%s, %s, %s)
                ON CONFLICT (head_record_card, employee_record_card)
                DO UPDATE SET rate_status = %s;
                """,
                (colleague_num,head_num,bool(status),bool(status))
            )