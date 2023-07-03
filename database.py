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
    
    def get_colleagues(self, head_service_number, admin):
        result = ''
        if admin == 0:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM employee
                    WHERE head_service_number = %s
                    """,
                    (head_service_number,)
                )
                result = cursor.fetchall()
        else:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT *
                    FROM employee
                    """
                )
                result = cursor.fetchall()
        return result


    def get_head_service_name(self, number):
        result = ''
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT fio_head_of_department
                FROM head_of_department
                WHERE head_service_number = %s
                """,
                (number,)
            )
            result = cursor.fetchall()
        if result:
            return result[0][0]
        return ''
