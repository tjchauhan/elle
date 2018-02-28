import os
import shutil
import json
import datetime
import soundfile as sf
from bcrypt import hashpw, checkpw, gensalt
from flask_sslify import SSLify
from flask import Flask, render_template, request, send_file, Response, after_this_request, jsonify, send_from_directory
from flask_restful import Resource, Api, reqparse
from flaskext.mysql import MySQL
from flask_jwt import JWT, jwt_required, current_identity, _default_request_handler
from resources.user import UserRegister
from models.user import User
from models.admin import Admin
from models.language import LanguageModel
from resources.log import PlayerLog, GroupLog, LogOverview, LogPostTest
from resources.player import Player, PlayerList
from resources.language import Language, LanguageList, LanguageByAuthor
from resources.admin import PendingAdmin, ApproveAdmin, DenyAdmin
from resources.group import Group, GroupMember
from db import mysql
from security import authenticate, identity

app = Flask(__name__)
app.config['MYSQL_DATABASE_USER'] = 'tyler'
app.config['MYSQL_DATABASE_PASSWORD'] = '' # Get passsword from Dr Johnson
app.config['MYSQL_DATABASE_DB'] = 'elle_test_2'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['JWT_EXPIRATION_DELTA'] = datetime.timedelta(minutes=60)

app.secret_key = 'tyler'
mysql.init_app(app)
api = Api(app)

jwt = JWT(app, authenticate, identity)

@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/imageUpdate")
def image_update():
    return render_template("updateImage.html")

@app.route('/signUp')
def signUp():
    return render_template('signup.html')

@app.route('/signUpUser', methods=['POST'])
def signUpUser():
    user =  request.form['username']
    password = request.form['password']

    if User.find_by_username(user):
        return {"message": "A user with that username already exists"}, 400

    pw_hash = hashpw(password.encode('utf8'), gensalt())
    conn = mysql.connect()
    cursor = conn.cursor()
    query = "INSERT INTO users VALUES (uuid(), %s, %s, %s, %s)"
    cursor.execute(query, (user, pw_hash, 'sample@test.com', 0))
    conn.commit()
    conn.close()

    return {'status':'OK','user':user,'pass':password}

@app.route('/file-downloads/')
def file_downloads():
	try:
		return render_template('downloads.html')
	except Exception as e:
		return str(e)

@app.route('/termUpload')
def term_upload():
	try:
		return render_template('term.html')
	except Exception as e:
		return str(e)

class ConvertOGG(Resource):
    def get(self):
        try:
            for filename in os.listdir('/srv/portuguese/'):
                if filename.endswith(".wav"):
                    data, samplerate = sf.read('/srv/portuguese/' + filename)
                    sf.write('/srv/portuguese/' + filename[:-4] + '.ogg', data, samplerate)
                    os.remove('/srv/portuguese/' + filename)
            return {'message': 'successful'}
        except Exception as e:
    		return str(e)

class Download(Resource):
    def get(self, lang):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM vocabulary WHERE lang_name=%s"
        terms = []
        lang_dir = lang.replace(" ", "").lower()
        cursor.execute(query, (lang.lower(),))
        result = cursor.fetchall()

        if result:
            for row in result:
                terms.append({'term': row[1].encode('utf-8'), 'difficulty': row[2], 'translation': row[3], 'image': row[4].encode('utf-8'), 'audio_term': row[5].encode('utf-8'), 'audio_translation': row[6].encode('utf-8'), 'tag': row[7]})

            version_query = "SELECT version FROM languages WHERE lang_name=%s"
            cursor.execute(version_query, (lang,))
            version_result = cursor.fetchone()

            with open("/srv/" + lang_dir + "/terms.json", 'w') as file:
                module_info = {'language': lang, 'version': version_result[0], 'terms': terms}
                file.write(json.dumps(module_info))
                file.close()

            shutil.make_archive('/srv/' + lang_dir, 'zip', '/srv/' + lang_dir)

            @after_this_request
            def delete_zip(response):
                try:
                    os.remove('/srv/' + lang_dir + '.zip')
                    os.remove('/srv/' + lang_dir + '/terms.json')
                    return(response)
                except Exception as e:
                    return str(e)

            return send_file('/srv/' + lang_dir + '.zip',
                    mimetype = 'zip',
                    attachment_filename= lang_dir + '.zip',
                    as_attachment = True)
        else:
            return {'error': 'There is no module with this name'}

class Upload(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('lang_name',
        type=str,
        required=True,
        help="lang_name cannot be left blank."
    )
    parser.add_argument('term',
        type=str,
        required=True,
        help="term cannot be left blank."
    )

    @classmethod
    def term_in_db(cls, lang_name, term):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM vocabulary WHERE lang_name=%s AND term=%s"
        cursor.execute(query, (lang_name, term))
        if cursor.fetchall():
            conn.commit()
            conn.close()
            return True
        else:
            conn.commit()
            conn.close()
            return False

    @jwt_required()
    def post(self):
        term = request.form.get("term")
        lang = request.form.get("lang")
        difficulty = request.form.get("difficulty")
        translation = request.form.get("translation")
        tag = request.form.get("tag")

        conn = mysql.connect()
        cursor = conn.cursor()

        target = '/srv/' + lang.replace(" ", "").lower()

        if Upload.term_in_db(lang, term):
            return {'message': 'This term has already been uploaded.'}

        if not os.path.isdir(target):
            os.mkdir(target)

        filenames = []
        ogg_filenames = []
        audio = ["_term", "_translation"]
        i = 0
        for file in request.files.getlist("file"):
            ext = file.filename[-4:]
            if ext == ".png":
                filename = term.replace(" ", "").lower() + ext
            else:
                filename = term.replace(" ", "").lower() + audio[i] + ext
                i += 1
                ogg_filenames.append(filename[:-4] + '.ogg')
            destination = "/".join([target, filename])
            file.save(destination.encode('utf-8'))
            filenames.append(filename)

        query = "INSERT INTO vocabulary VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (lang.lower(), term.lower().encode('utf-8'), difficulty, translation.lower(), filenames[0].encode('utf-8'), filenames[1].encode('utf-8'), filenames[2].encode('utf-8'), tag))
        conn.commit()
        update_version = "UPDATE languages SET version = version + 1 WHERE lang_name=%s"
        cursor.execute(update_version, (lang.lower(),))
        conn.commit()
        conn.close()

        return {'message': 'Term upload successful'}

    @jwt_required()
    def delete(self):
        data = Upload.parser.parse_args()
        token_second_segment = _default_request_handler().split('.')[1]
        admin = Admin.is_admin(token_second_segment)
        if admin.isAdmin:
            conn = mysql.connect()
            cursor = conn.cursor()
            query = "DELETE vocabulary FROM vocabulary INNER JOIN languages ON languages.lang_name=vocabulary.lang_name WHERE languages.author=%s AND vocabulary.lang_name=%s AND vocabulary.term=%s"
            cursor.execute(query, (admin.username, data['lang_name'], data['term']))
            conn.commit()
            conn.close()

            os.remove('/srv/' + data['lang_name'].lower() + '/' + data['term'].lower() + '.png')
            os.remove('/srv/' + data['lang_name'].lower() + '/' + data['term'].lower() + '_term.ogg')
            os.remove('/srv/' + data['lang_name'].lower() + '/' + data['term'].lower() + '_translation.ogg')

            return {'message': 'Term successfully deleted'}
        else:
            return {'error': 'You are not an admin'}

class Test(Resource):
    @jwt_required()
    def get(self):
        return {'message': 'You are logged in.'}

class Test_Identity(Resource):
    @jwt_required()
    def get(self):
        token_second_segment = _default_request_handler().split('.')[1]
        if Admin.is_admin(token_second_segment).isAdmin:
            return {'message': 'You are an admin'}
        else:
            return {'error': 'You are not an admin'}, 403

class Term(Resource):
    @jwt_required()
    def get(self, language, term):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM vocabulary WHERE lang_name=%s AND term=%s"
        cursor.execute(query, (language, term.encode('utf8')))
        result = cursor.fetchall()

        if result:
            term = []
            for row in result:
                term.append({'lang_name': row[0], 'term': row[1].ecode('utf8'), 'difficulty': row[2], 'translation': row[3], 'tag': row[7]})

            conn.close()

            return {'term_info': term}
        else:
            conn.close()
            return {'message': 'This term is not in the database'}

class ResetPassword(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('password_reset',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('new_password',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('email',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )

    def put(self):
        data = ResetPassword.parser.parse_args()
        user = User.find_by_username(data['username'])
        if user and checkpw(data['password_reset'].encode('utf8'), user.password_reset.encode('utf8')) and (data['email']==user.email):
            conn = mysql.connect()
            cursor = conn.cursor()
            query = "UPDATE users SET password=%s WHERE username=%s AND email=%s"

            pw_hash = hashpw(data['new_password'], gensalt())

            cursor.execute(query, (pw_hash, data['username'], data['email']))
            conn.commit()
            conn.close()
            return {'message': 'Password has been reset'}
        else:
            return {'error': 'password reset is incorrect'}

class TermFiles(Resource):
    def get(self, language, filename):
        lang_name = language.replace(" ", "").lower()
        directory = "/srv/" + lang_name + "/"
        return send_from_directory(directory, filename, as_attachment=True)

class TermsInLanguage(Resource):
    @jwt_required()
    def get(self, language):
        if LanguageModel.check_lang_v2(language):
            conn = mysql.connect()
            cursor = conn.cursor()
            query = "SELECT term, translation, difficulty, tag FROM vocabulary WHERE lang_name=%s"
            cursor.execute(query, (language,))
            result = cursor.fetchall()

            terms = []

            for row in result:
                terms.append({'term': row[0].encode('utf8'), 'translation': row[1], 'difficulty': row[2], 'tag': row[3]})

            conn.close()

            return {'terms': terms}
        else:
            return {'error': 'This is not a valid language'}

class TermFieldEdit(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('lang_name',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('term',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('translation',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('difficulty',
        type=int,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('tag',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )

    @jwt_required()
    def put(self):
        data = TermFieldEdit.parser.parse_args()
        conn = mysql.connect()
        cursor = conn.cursor()
        if Upload.term_in_db(data['lang_name'], data['term']):
            query = "UPDATE vocabulary SET translation=%s, difficulty=%s, tag=%s WHERE lang_name=%s AND term=%s"
            cursor.execute(query, (data['translation'],data['difficulty'], data['tag'], data['lang_name'], data['term'].encode('utf-8')))
            conn.commit()
            conn.close()
            return {'message': 'Term updated successfully'}
        else:
            {'error': 'This term is not already in the database'}

class TermImageEdit(Resource):
    @jwt_required()
    def post(self, language, term):
        if Upload.term_in_db(language, term):
            target = "/srv/" + language.replace(" ", "").lower()
            filenames = []
            for file in request.files.getlist("file"):
                ext = file.filename[-4:]
                if ext == ".png":
                    filename = term.replace(" ", "").lower() + ext
                else:
                    return {'error': 'This image is not the right format'}
                destination = "/".join([target, filename])
                file.save(destination.encode('utf-8'))
                filenames.append(filename)

            return {'message': 'Image file successfully updated'}
        else:
            return {'error': 'Term not already in the database'}

class TermAudioEdit(Resource):
    @jwt_required()
    def post(self, language, term):
        target = "/srv/" + language.replace(" ", "").lower()
        filenames = []
        for file in request.files.getlist("file"):
            ext = file.filename[-4:]
            if ext == ".ogg":
                filename = term.replace(" ", "").lower() + "_term" + ext
            else:
                return {'error': 'This file is not the right format'}
            destination = "/".join([target, filename])
            file.save(destination.encode('utf-8'))
            filenames.append(filename)
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "UPDATE vocabulary SET audio1=%s WHERE lang_name=%s AND term=%s"
        cursor.execute(query, (filenames[0].encode('utf-8'), language, term))
        conn.commit()
        conn.close()

        return {'message': 'Term audio file successfully updated'}

class TranslationAudioEdit(Resource):
    @jwt_required()
    def post(self, language, term):
        target = "/srv/" + language.replace(" ", "").lower()
        filenames = []
        for file in request.files.getlist("file"):
            ext = file.filename[-4:]
            if ext == ".ogg":
                filename = term.replace(" ", "").lower() + "_translation" + ext
            else:
                return {'error': 'This file is not the right format'}
            destination = "/".join([target, filename])
            file.save(destination.encode('utf-8'))
            filenames.append(filename)
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "UPDATE vocabulary SET audio2=%s WHERE lang_name=%s AND term=%s"
        cursor.execute(query, (filenames[0].encode('utf-8'), language, term))
        conn.commit()
        conn.close()

        return {'message': 'Translation audio file successfully updated'}

api.add_resource(Test, '/test')
api.add_resource(ConvertOGG, '/convertOgg')
api.add_resource(Test_Identity, '/test2')
api.add_resource(Upload, '/upload')
api.add_resource(Language, '/lang')
api.add_resource(LanguageList, '/langlist')
api.add_resource(LanguageByAuthor, '/langByAuthor')
api.add_resource(TermsInLanguage, '/langTerms/<string:language>')
api.add_resource(UserRegister, '/register')
api.add_resource(PendingAdmin, '/pendingAdmin')
api.add_resource(ApproveAdmin, '/approveAdmin')
api.add_resource(DenyAdmin, '/denyAdmin')
api.add_resource(Player, '/player')
api.add_resource(PlayerList, '/playerList')
api.add_resource(Group, '/group')
api.add_resource(GroupMember, '/groupMember/<string:groupName>')
api.add_resource(PlayerLog, '/log/player/<string:username>')
api.add_resource(GroupLog, '/log/group/<string:groupName>')
api.add_resource(LogOverview, '/logOverview')
api.add_resource(LogPostTest, '/logTest')
api.add_resource(Download, '/download/<string:lang>')
api.add_resource(Term, '/term/<string:language>/<string:term>')
api.add_resource(ResetPassword, '/resetPassword')
api.add_resource(TermFieldEdit, '/termFieldEdit')
api.add_resource(TermImageEdit, '/termImageEdit/<string:language>/<string:term>')
api.add_resource(TermAudioEdit, '/termAudioEdit/<string:language>/<string:term>')
api.add_resource(TranslationAudioEdit, '/translationAudioEdit/<string:language>/<string:term>')
api.add_resource(TermFiles, '/termFiles/<string:language>/<string:filename>')

if __name__ == "__main__":
    app.run()
