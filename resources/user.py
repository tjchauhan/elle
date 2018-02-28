from bcrypt import hashpw, checkpw, gensalt
from flask_restful import Resource, reqparse
from ..models.user import User
from flaskext.mysql import MySQL
from ..db import mysql

class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('password',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('email',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('isAdmin',
        type=int,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('password_reset',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('sex',
        type=str,
        required=False,
    )
    parser.add_argument('age',
        type=int,
        required=False,
    )
    parser.add_argument('motivation',
        type=str,
        required=False,
    )

    def post(self):
        data = UserRegister.parser.parse_args()

        if data['isAdmin'] == 0 and (data['sex'] is None or data['age'] is None or data['motivation'] is None):
            return {'message': 'Either sex, age, or motivation were not entered.'}

        if User.find_by_username(data['username']):
            return {"message": "A user with that username already exists"}, 400

        pw_hash = hashpw(data['password'], gensalt())
        pw_reset_hash = hashpw(data['password_reset'], gensalt())
        conn = mysql.connect()
        cursor = conn.cursor()
        user_query = "INSERT INTO users VALUES (%s, %s, %s, %s, uuid(), %s)"
        cursor.execute(user_query, (data['username'], pw_hash, data['email'], data['isAdmin'], pw_reset_hash.encode('utf8')))
        conn.commit()

        if data['isAdmin'] == 0:
            player_query = "INSERT INTO players VALUES (%s, %s, %s, %s)"
            cursor.execute(player_query, (data['username'], data['sex'], data['age'], data['motivation']))
            conn.commit()

        conn.close()

        return {'message': 'User created successfully.'}, 201
