from flaskext.mysql import MySQL
from ..db import mysql

class Log:
    def __init__(self, username, lang_name, lang_version, score, puzzles_attempted, game_type):
        self.username = username
        self.lang_name = lang_name
        self.lang_version = lang_version
        self.score = score
        self.puzzles_attempted = puzzles_attempted
        self.game_type = game_type

    @classmethod
    def save_to_db(cls, log):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "INSERT INTO logs VALUES (NULL, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (log.lang_name.lower(), log.username, log.score, log.puzzles_attempted, log.lang_version, log.game_type))
        conn.commit()
        conn.close()

    @classmethod
    def find_logs_by_username(cls, username):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM logs WHERE username=%s"
        cursor.execute(query, (username,))
        result = cursor.fetchall()
        logs = []
        for row in result:
            logs.append({'logID': row[0], 'lang_name': row[1],'lang_version': row[5], 'score': row[3], 'puzzles_attempted': row[4], 'game_type': row[6]})
        conn.close()

        return logs
