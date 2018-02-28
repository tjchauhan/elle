from flaskext.mysql import MySQL
from ..db import mysql

class User:
    def __init__(self, username, password, email, isAdmin, _id, password_reset):
        self.username = username
        self.password = password
        self.email = email
        self.isAdmin = isAdmin
        self.id = _id
        self.password_reset = password_reset

    @classmethod
    def find_by_username(cls, username):
        conn = mysql.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM users WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row:
            user = cls(*row)
        else:
            user = None

        conn.close()
        return user

    @classmethod
    def find_by_id(cls, _id):
        conn = mysql.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM users WHERE loginKey=%s"
        cursor.execute(query, (_id,))
        row = cursor.fetchone()
        if row:
            user = cls(*row)
        else:
            user = None

        conn.close()
        return user

    @classmethod
    def find_by_email(cls, email):
        conn = mysql.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM users WHERE email=%s"
        cursor.execute(query, (email,))
        row = cursor.fetchone()
        if row:
            user = cls(*row)
        else:
            user = None

        conn.close()
        return user
