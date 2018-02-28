import shutil
from flask_restful import Resource, reqparse
from flask_jwt import jwt_required, _default_request_handler
from ..models.language import LanguageModel
from ..models.admin import Admin
from ..db import mysql

class Language(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('lang_name',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('version',
        type=str,
        required=False,
        help="This field cannot be left blank."
    )

    @jwt_required()
    def post(self):
        data = Language.parser.parse_args()
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            language = LanguageModel(admin.username, **data)
            if not LanguageModel.check_lang(language):
                LanguageModel.save_to_db(language)
                return {'message': 'Language created successfully.'}, 201
            else:
                return {'message': 'Language already created.'}
        else:
            return {'error': 'You are not an admin'}, 403

    @jwt_required()
    def delete(self):
        data = Language.parser.parse_args()
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)

        if LanguageModel.check_author(data['lang_name']) == admin.username:

            conn = mysql.connect()
            cursor = conn.cursor()
            delete_terms_query = "DELETE FROM vocabulary WHERE lang_name=%s"
            cursor.execute(delete_terms_query, (data['lang_name'],))
            query = "DELETE FROM languages WHERE lang_name=%s and author=%s"
            cursor.execute(query, (data['lang_name'], admin.username))
            conn.commit()
            conn.close()

            shutil.rmtree('/srv/' + data['lang_name'].replace(" ", "").lower())

            return {'message': 'Language successfully deleted'}

        else:
            return {'message': 'You cannot delete this language because you are not the author'}

class LanguageList(Resource):

    @jwt_required()
    def get(self):
        modules = LanguageModel.get_lang_list()

        return {'modules': modules}

class LanguageByAuthor(Resource):
    @jwt_required()
    def get(self):
        conn = mysql.connect()
        cursor = conn.cursor()
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        query = "SELECT languages.lang_name, languages.version, languages.author, COUNT(vocabulary.term) FROM languages LEFT JOIN vocabulary ON languages.lang_name=vocabulary.lang_name WHERE author=%s GROUP BY lang_name"
        cursor.execute(query, (admin.username,))
        result = cursor.fetchall()
        languages = []

        for row in result:
            languages.append({'lang_name': row[0], 'version': row[1], 'num_terms': row[3]})

        conn.close()

        return {'langauges': languages}
