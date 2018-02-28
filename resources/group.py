from flask_restful import Resource, Api, reqparse
from flaskext.mysql import MySQL
from flask_jwt import jwt_required, _default_request_handler
from ..db import mysql
from ..models.admin import Admin
from ..models.user import User

class Group(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('groupName',
        type=str,
        required=True,
        help="groupName cannot be left blank."
    )

    @jwt_required()
    def post(self):
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            data = Group.parser.parse_args()

            conn = mysql.connect()
            cursor = conn.cursor()
            check_group = "SELECT * FROM groups WHERE groupName=%s"
            query = "INSERT INTO groups VALUES (NULL, %s, %s)"
            cursor.execute(check_group, (data['groupName'],))
            result = cursor.fetchall()
            if not result:
                cursor.execute(query, (data['groupName'], admin.username))
                conn.commit()
                conn.close()

                return {'message': 'Group created successfully.'}
            else:
                conn.close()
                return {'message': 'There is already a group with this name'}
        else:
            return {'error': 'You are not an admin'}

    @jwt_required()
    def get(self):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM groups"
        cursor.execute(query)
        result = cursor.fetchall()

        groups = []
        for row in result:
            groups.append({'groupName': row[1], 'admin': row[2]})

        conn.commit()
        conn.close()

        return {'groups': groups}

    @jwt_required()
    def delete(self):
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            data = Group.parser.parse_args()
            conn = mysql.connect()
            cursor = conn.cursor()
            check_group = "SELECT * FROM groups WHERE groupName=%s AND admin=%s"
            query = "DELETE FROM groups WHERE groupName=%s AND admin=%s"
            cursor.execute(check_group, (data['groupName'],admin.username))
            result = cursor.fetchall()
            if result:
                cursor.execute(query, (data['groupName'], admin.username))
                conn.commit()
                conn.close()

                return {'message': 'Group successfully deleted'}
            else:
                return {'error': 'You are not this group\'s admin'}
        else:
            return {'error': 'You are not an admin'}

class GroupMember(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="username cannot be left blank."
    )

    @jwt_required()
    def post(self, groupName):
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            data = GroupMember.parser.parse_args()

            conn = mysql.connect()
            cursor = conn.cursor()
            get_groupID = "SELECT groupID FROM groups WHERE groupName=%s and admin=%s"
            cursor.execute(get_groupID, (groupName, admin.username))
            result = cursor.fetchall()
            if result:
                player = User.find_by_username(data['username'])
                if player:
                    groupID = result[0]
                    check_player = "SELECT * FROM group_members WHERE groupID=%s AND username=%s"
                    query = "INSERT INTO group_members VALUES (%s, %s)"
                    cursor.execute(check_player, (groupID, data['username']))
                    result = cursor.fetchall()
                    if not result:
                        cursor.execute(query, (groupID, data['username']))
                        conn.commit()
                        conn.close()

                        return {'message': 'Player added to group.'}
                    else:
                        return {'error': 'Player already in group'}
                else:
                    return {'error': 'This player is not registered'}
            else:
                return {'error': 'You are not this group\'s admin'}
        else:
            return {'error': 'You are not an admin'}, 403

    @jwt_required()
    def get(self, groupName):
        conn = mysql.connect()
        cursor = conn.cursor()
        get_groupID = "SELECT groupID FROM groups WHERE groupName=%s"
        cursor.execute(get_groupID, (groupName,))
        result = cursor.fetchall()
        groupID = result[0]

        query = "SELECT * FROM group_members WHERE groupID=%s"
        cursor.execute(query, (groupID,))
        result = cursor.fetchall()

        members = []

        for row in result:
            members.append({'username': row[1]})

        conn.close()
        return {'num_members': len(members), 'members': members}

    @jwt_required()
    def delete(self, groupName):
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            data = GroupMember.parser.parse_args()

            conn = mysql.connect()
            cursor = conn.cursor()
            get_groupID = "SELECT groupID FROM groups WHERE groupName=%s and admin=%s"
            cursor.execute(get_groupID, (groupName, admin.username))
            result = cursor.fetchall()
            if result:
                groupID = result[0]
                delete_query = "DELETE FROM group_members WHERE groupID=%s AND username=%s"
                cursor.execute(delete_query, (groupID, data['username']))
                conn.commit()
                conn.close()
                return {'message': 'Player removed from group'}
            else:
                return {'error': 'Either you are not this group\'s admin or this group does not exist'}
        else:
            return {'error': 'You are not an admin'}, 403
