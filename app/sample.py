from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os, json, redis

# App
application = Flask(__name__)

# connect to MongoDB
mongoClient = MongoClient('mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ['MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_AUTHDB'])
db = mongoClient[os.environ['MONGODB_DATABASE']]

col_game = db.game

# connect to Redis
redisClient = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get("REDIS_PORT", 6379), db=os.environ.get("REDIS_DB", 0))

@application.route('/')
def index():
    col_game.delete_many({})
    col_game.insert({
    "step":0,
    "count":0,
    "answer": [],
    "hint": ["*","*","*","*"],
    "guess": [],
    "status":0
    })
    return render_template('index.html')

@application.route('/start', methods=["GET"])
def start():
    game = col_game.find_one()
    if game == None:
        return render_template('index.html')
    return render_template('start.html', game=game)

@application.route('/start', methods=["POST"])
def create_ans():
    game = col_game.find_one()
    
    if game["step"] <= 3:
        game["answer"].append(request.form['choice'])
        col_game.update_one({}, {
            '$set': {
                "step": game["step"] + 1,
                "answer": game["answer"]
            }
        })
    return render_template('start.html', game=game)

@application.route('/play', methods=["GET"])
def play_get():
    game = col_game.find_one()
    return render_template('play.html', game=game)

@application.route('/play', methods=["POST"])
def play_post():
    game = col_game.find_one()

    if game["step"] <= 7:
        game["guess"].append(request.form['choice'])
        col_game.update_one({}, {
            '$set': {
                "step": game["step"] + 1,
                "guess": game["guess"]
            }
        })
    return render_template('play.html', game=game)

@application.route('/result', methods=["GET"])
def result():
    game = col_game.find_one()
    return render_template('result.html', game=game)

@application.route('/check', methods=["GET"])
def check():
    game = col_game.find_one()

    ans = game["answer"]
    guess = game["guess"]
    new_guess = []
    new_hint = []
    correct = True

    for i in range(4):
        if (ans[i] == guess[i]):
            new_hint.append(ans[i])
        else:
            new_hint.append("*")
            correct = False
    col_game.update_one({}, {"$set": {"count": game["count"]+1, "step": 4, "hint": new_hint, "guess": new_guess}})
    game = col_game.find_one()
    if correct:
        return render_template('result.html', game=game)
    return render_template('play.html', game=game)

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("FLASK_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("FLASK_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
