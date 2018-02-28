from flask_restful import Resource, reqparse
from flask_jwt import jwt_required
from ..models.player import PlayerModel

class Player(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('sex',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('age',
        type=int,
        required=True,
        help="This field cannot be left blank."
    )
    parser.add_argument('motivation',
        type=str,
        required=True,
        help="This field cannot be left blank."
    )

    def post(self):
        data = Player.parser.parse_args()
        player = PlayerModel(**data)

        PlayerModel.save_to_db(player)

        return {'message': 'Player created successfully.'}, 201

class PlayerList(Resource):

    @jwt_required()
    def get(self):
        players = PlayerModel.get_player_list()

        return {'players': players}
