from flaskext.mysql import MySQL
from ..db import mysql

class PlayerModel:
    def __init__(self, username, sex, age, motivation):
        self.username = username
        self.sex = sex
        self.age = age
        self.motivation = motivation

    @classmethod
    def save_to_db(cls, player):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "INSERT INTO players VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (player.username, player.sex, player.age, player.motivation))
        conn.commit()
        conn.close()

    @classmethod
    def get_player_list(self):
        conn = mysql.connect()
        cursor = conn.cursor()
        query = "SELECT * FROM players"
        cursor.execute(query)
        result = cursor.fetchall()
        players = []

        for row in result:
            players.append({'username': row[0], 'sex': row[1], 'age': row[2], 'motivation': row[3]})

        conn.close()

        return players
