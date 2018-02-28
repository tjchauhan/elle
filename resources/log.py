import json
from flask_restful import Resource, reqparse
from flask_jwt import jwt_required, _default_request_handler
from ..models.log import Log
from ..models.user import User
from flaskext.mysql import MySQL
from ..db import mysql

class PlayerLog(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('lang_name',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('lang_version',
        type=int,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('score',
        type=int,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('puzzles_attempted',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('game_type',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )

    @jwt_required()
    def get(self, username):
        try:
            if User.find_by_username(username):
                logs = Log.find_logs_by_username(username)
                return {'logs': logs}
            else:
                return {'message': 'Username does not exist.'}
        except Exception as e:
    		return str(e)

    @jwt_required()
    def post(self, username):
        data = PlayerLog.parser.parse_args()
        log = Log(username, **data)

        Log.save_to_db(log)

        return {'message': 'Log created successfully.'}, 201

class GroupLog(Resource):
    @jwt_required()
    def get(self, groupName):
        try:
            conn = mysql.connect()
            cursor = conn.cursor()
            get_groupID = "SELECT groupID FROM groups WHERE groupName=%s"
            cursor.execute(get_groupID, (groupName,))
            result = cursor.fetchall()
            groupID = result[0]

            get_Players = "SELECT username FROM group_members WHERE groupID=%s"
            cursor.execute(get_Players, (groupID,))
            usernames = cursor.fetchall()

            group_logs = []

            query = "SELECT * FROM logs WHERE username=%s"
            for row in usernames:
                cursor.execute(query, (row[0]))
                logs = cursor.fetchall()
                for log in logs:
                    group_logs.append({'logID': log[0], 'username': log[2], 'score': log[3], 'puzzles_attempted': log[4], 'lang_name': log[1], 'lang_version': log[5], 'game_type': log[6]})

            return {'logs': group_logs}
        except Exception as e:
    		return str(e)

class LogOverview(Resource):
    @jwt_required()
    def get(self):
        try:
            conn = mysql.connect()
            cursor = conn.cursor()
            query = "SELECT l.username, p.sex, p.age, l.lang_name, COUNT(l.username), AVG(l.score) as average FROM logs AS l INNER JOIN players AS p ON l.username = p.username GROUP BY l.username, l.lang_name"
            cursor.execute(query)
            result = cursor.fetchall()

            logs = []

            for row in result:
                logs.append({'username': row[0], 'sex': row[1], 'age': row[2], 'lang_name': row[3], 'count': row[4], 'average': float(row[5])})

            return {'logs': logs}
        except Exception as e:
    		return str(e)

class LogPostTest(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('lang_name',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('score',
        type=int,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('puzzles_attempted',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )

    @jwt_required()
    def post(self):
        try:
            token_second_segment = _default_request_handler().split('.')[1]
            payload = json.loads(token_second_segment.decode('base64'))
            usr = User.find_by_id(payload['identity'])
            data = PlayerLog.parser.parse_args()
            log = Log(usr.username, **data)

            Log.save_to_db(log)

            return {'message': 'Log created successfully.'}, 201
        except Exception as e:
    		return str(e)
