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
    
    def get_colleagues(self, head_report_card, admin):
        result = ''
        if admin == 0:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM staff
                    WHERE head_report_card = %s
                    """,
                    (head_report_card,)
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
                WHERE employee_record_card IN (SELECT DISTINCT head_report_card FROM staff);
                """
                )
            result = cursor.fetchall()
        return dict(result)
    
    def get_num_record_userinfo(self, number):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT employee_full_name, department_position, department
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
                'department_position': result[0][1]
            }
        return infodict
    

    def get_criterias_name(self, staff_num):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.criterion, c.description
                FROM staff s
                JOIN criteria c ON s.department = c.department
                            AND s.department_position = c.department_position
                WHERE s.employee_record_card = %s;""",
                (staff_num,)
            )
            result = cursor.fetchall()
        return result
