from user import User
import json
from flaskext.mysql import MySQL
from ..db import mysql

class Admin:

    @classmethod
    def is_admin(cls, token):
        payload = json.loads(token.decode('base64'))
        usr = User.find_by_id(payload['identity'])
        return usr

    @classmethod
    def find_by_username(cls, username):
        return User.find_by_username(username)

    @classmethod
    def find_by_email(cls, email):
        return User.find_by_email(email)

    @classmethod
    def find_pending_by_username(cls, username):
        conn = mysql.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM pending_admins WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return True
        else:
            return False

    @classmethod
    def find_pending_by_email(cls, email):
        conn = mysql.connect()
        cursor = conn.cursor()

        query = "SELECT * FROM pending_admins WHERE email=%s"
        cursor.execute(query, (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return True
        else:
            return False
