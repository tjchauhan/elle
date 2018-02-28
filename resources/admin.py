from ..models.admin import Admin
from flask_restful import Resource, reqparse
from flaskext.mysql import MySQL
from ..db import mysql
from flask_jwt import jwt_required, _default_request_handler
from bcrypt import hashpw, checkpw, gensalt

class PendingAdmin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="username cannot be left blank."
    )
    parser.add_argument('password',
        type=str,
        required=True,
        help="password cannot be left blank."
    )
    parser.add_argument('email',
        type=str,
        required=True,
        help="admin cannot be left blank."
    )
    parser.add_argument('sent_by',
        type=str,
        required=True,
        help="sent_by cannot be left blank."
    )
    parser.add_argument('password_reset',
        type=str,
        required=True,
        help="password_reset cannot be left blank."
    )

    @jwt_required()
    def get(self):
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)

        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM pending_admins WHERE sent_by=%s"
        cursor.execute(query, (admin.username))
        result = cursor.fetchall()

        pendings = []

        for row in result:
            pendings.append({'username': row[0], 'email': row[2]})

        return {'pending_admins': pendings}

    def post(self):
        data = PendingAdmin.parser.parse_args()
        pw_hash = hashpw(data['password'], gensalt())
        pw_reset_hash = hashpw(data['password_reset'], gensalt())

        if Admin.find_by_username(data['username']) or Admin.find_pending_by_username(data['username']):
            return {"message": "An admin with that username already exists"}, 400

        if Admin.find_by_email(data['email']) or Admin.find_pending_by_email(data['email']):
            return {"message": "An admin with that email already exists"}, 400

        if not Admin.find_by_username(data['sent_by']):
            return {"message": "This admin does not exist."}, 400

        conn = mysql.connect()
        cursor = conn.cursor()
        query = "INSERT INTO pending_admins VALUES (%s, %s, %s, %s, %s)"
        cursor.execute(query, (data['username'], pw_hash, data['email'], data['sent_by'], pw_reset_hash))
        conn.commit()
        conn.close()

        return {'message': 'Admin profile creation is pending approval'}

class ApproveAdmin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="username cannot be left blank."
    )

    @jwt_required()
    def post(self):
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            data = ApproveAdmin.parser.parse_args()

            conn = mysql.connect()
            cursor = conn.cursor()

            if not Admin.find_pending_by_username(data['username']):
                return {'message': 'There is no pending admin associated with this username'}

            get_query = "SELECT * FROM pending_admins WHERE username=%s AND sent_by=%s"
            cursor.execute(get_query, (data['username'], admin.username))
            result = cursor.fetchone()
            post_query = "INSERT INTO users VALUES (%s, %s, %s, 1, uuid(), %s)"
            cursor.execute(post_query, (result[0], result[1], result[2], result[4]))
            conn.commit()

            delete_query = "DELETE FROM pending_admins WHERE username=%s"
            cursor.execute(delete_query, (data['username'],))
            conn.commit()
            conn.close()

            return {'message': 'Approved as an admin'}
        else:
            return {'message': 'You are not an admin'}

class DenyAdmin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="username cannot be left blank."
    )

    @jwt_required()
    def delete(self):
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            data = ApproveAdmin.parser.parse_args()

            conn = mysql.connect()
            cursor = conn.cursor()
            query = "DELETE FROM pending_admins WHERE username=%s AND sent_by=%s"
            cursor.execute(query, (data['username'], admin.username))
            conn.commit()
            conn.close()

            return {'message': 'Pending admin has been denied'}
        else:
            return {'error': 'You are not an admin'}, 403
