from flaskext.mysql import MySQL
from ..db import mysql

class LanguageModel:
    def __init__(self, author, lang_name, version):
        self.author = author
        self.lang_name = lang_name
        self.version = version

    @classmethod
    def check_lang(cls, language):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM languages WHERE lang_name=%s"
        cursor.execute(query, (language.lang_name.lower(),))
        if cursor.fetchall():
            return True
        else:
            return False

    @classmethod
    def check_lang_v2(cls, language):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM languages WHERE lang_name=%s"
        cursor.execute(query, (language.lower(),))
        if cursor.fetchall():
            return True
        else:
            return False

    @classmethod
    def save_to_db(cls, language):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "INSERT INTO languages VALUES (%s, %s, %s)"
        cursor.execute(query, (language.lang_name.lower().encode('utf8'), language.version, language.author))
        conn.commit()
        conn.close()

    @classmethod
    def get_lang_list(self):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT languages.lang_name, languages.version, languages.author, COUNT(vocabulary.term) FROM languages LEFT JOIN vocabulary ON languages.lang_name=vocabulary.lang_name GROUP BY lang_name"
        cursor.execute(query)
        result = cursor.fetchall()
        modules = []
        for row in result:
            modules.append({'lang_name': row[0], 'version': row[1], 'author': row[2], 'num_terms': row[3]})

        conn.close()

        return modules

    @classmethod
    def check_author(self, lang_name):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM languages WHERE lang_name=%s"
        cursor.execute(query, (lang_name,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[2]
        else:
            return False
