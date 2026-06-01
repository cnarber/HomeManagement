from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
import sqlite3
from notifypy import Notify
import uuid
import os, json
from bgg_request import BGG
from datetime import datetime, timedelta
from question_gen import generateTimesTable
from utils import get_user_from_ip

from werkzeug.exceptions import abort

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tester'

user_ips = {"127.0.0.1":"Daddy",
            "10.0.0.36":"FFour",
            "10.0.0.37":"FThree",
            "10.0.0.38":"FFive",
            "10.0.0.35":"FTwo",
            "10.0.0.31":"Mommy",
            "10.0.0.20":"Mommy",
            "10.0.0.33":"FOne",
            "192.168.1.7":"Parent"}

chores_list=["Dishwasher/Sink",
             "Stairwells",
            "Litter/Kitties",
             "Sweeping",
             "Mudroom"]

helping_list=["Dishwasher_Sink","Stairwells","Litter_Kitties","Sweeping","Mudroom",
              "Woke_Up_On_Own","Got_Ready_Quickly","Did_Homework","Took_Shower","Put_Away_Stuff",
              "Brushed_Teeth","Room_Clean","Practiced_Kickity_Punch","Dog_Food_Take_Out","Went_To_Bed_On_Time","Trash","Laundry","Work_with_Others"]

bad_list=["Disrespect","Not Listening","Loud","Fussing","Interrupting","Touching"]

kid_names = "FOne,FTwo,FThree,FFour,FFive".split(",")

question_timer = {}

user_game_requests = {}
user_movie_requests = {}
token = os.getenv("BGG_TOKEN")
bgg_user = os.getenv("BGG_USER")
bgg = BGG(token=token)
games = bgg.slim_game_collection(bgg_user)
for g in games:
    g['requests']=0

with open('movie_list.json', 'r') as f:
    movies = json.load(f)['movies']
for g in movies:
    g['requests']=0
    g['id']=g['id'].lstrip("0")

try:
    with open('play_requests.json', 'r') as f:
        user_game_requests = json.load(f)
        for u, list in user_game_requests.items():
            for game in games:
                if game['id'] in list:
                    game['requests'] += 1
except:
    print("no game request file")


movies = sorted(movies,key = lambda x:(x['name']))

leaderboard={}
with open('leaderboard.json', 'r') as f:
    leaderboard = json.load(f)

try:
    with open('watch_requests.json', 'r') as f:
        user_movie_requests = json.load(f)
        for u, list in user_movie_requests.items():
            for movie in movies:
                if movie['id'] in list:
                    movie['requests'] += 1
except:
    print("no movie request file")

empty_tick = {'K12': False, 'Attendance': False, 'Supplemental': False, 'IXL': False, 'Chore': False,'KUMON': False,
                         'Verified': False, 'Unfocused': 0, 'Fussy': 0, 'Issues': 0}
def load_ticks():
    tick_info = {u:{'K12':False,'Attendance':False,'Supplemental':False,'IXL':False,'KUMON': False,'Chore':False,'Verified':False,'Unfocused':0,'Fussy':0,'Issues':0} for u in user_ips.values()}
    day = datetime.now().strftime("%Y_%m_%d")
    try:
        with open('ticks/'+day+'.json', 'r') as f:
            tick_info = json.load(f)
    except:
        print("no tick info file")
    return day, tick_info

current_day, tick_info = load_ticks()

def check_ticks():
    global current_day
    day = datetime.now().strftime("%Y_%m_%d")
    if current_day!=day:
        current_day = day
        for u, info in tick_info.items():
            for k,v in empty_tick.items():
                info[k]=v

def save_ticks():
    day = datetime.now().strftime("%Y_%m_%d")
    with open('ticks/'+day+'.json', 'w') as f:
        json.dump(tick_info, f, indent=4)

all_letters = ['Requested','All','#']+[chr(v) for v in range(65,91)]


def summarize_ticks():
    days_in_week = []
    cd = datetime.now()
    cd = cd - timedelta(days=1)
    while cd.strftime("%A")!="Friday":
        days_in_week.append(cd.strftime("%Y_%m_%d"))
        cd = cd - timedelta(days=1)

    days_in_week = days_in_week[::-1]
    cd = datetime.now()
    days_in_week.append(cd.strftime("%Y_%m_%d"))
    while cd.strftime("%A")!="Friday":
        cd = cd + timedelta(days=1)
        days_in_week.append(cd.strftime("%Y_%m_%d"))

    tick_totals = {kn:[] for kn in kid_names}
    for day in days_in_week:
        try:
            with open('ticks/' + day + '.json', 'r') as f:
                cticks = json.load(f)
                for kn in kid_names:
                    tick_totals[kn].append(cticks[kn]['Unfocused']+cticks[kn]['Fussy']+cticks[kn]['Issues'])
        except:
            for kn in kid_names: tick_totals[kn].append('')
    total_list = []
    for i in range(7):
        total = 0
        for kn in kid_names:
            if tick_totals[kn][i]!='': total+=tick_totals[kn][i]
        total_list.append(total)
    tick_totals['Total']=total_list
    for k,list in tick_totals.items():
        list.append(sum([v for v in list if v !='']))
    return tick_totals

@app.route('/movies', methods=('GET', 'POST'))
def movies_page():
    query = request.args.get('q')  # Get the 'q' parameter
    if query is not None and query!='All':
        if query=='Requested':
            filtered_movies = sorted([g for g in movies if g['requests']>0],key = lambda x:(-x['requests'],x['name']))
        elif len(query)==0:
            filtered_movies = [g for g in movies if g['name'][0].isnumeric()]
        else:
            filtered_movies = [g for g in movies if g['name'][0] == query]
    else:
        filtered_movies = movies
    return render_template('movies.html', movies=filtered_movies, filters=all_letters)

@app.route('/review', methods=('GET', 'POST'))
def review_page():
    return render_template('review.html', leaderboard = leaderboard)


def getKidHelp():
    filedate = datetime.now().strftime("%Y_%m_%d")

    if not os.path.exists(f"goals/{filedate}.json"):
        kid_help = {}
        kid_bad = {}
        for i, kid in enumerate(kid_names):
            kid_help[kid] = {}
            kid_bad[kid] = {}
            for help in helping_list:
                kid_help[kid][help]=False
            for bad in bad_list:
                kid_bad[kid][bad]=False
        with open(f"goals/{filedate}.json", mode='w') as f:
            json.dump([kid_help,kid_bad], f, indent=4)
    else:
        with open(f"goals/{filedate}.json") as f:
            kid_help,kid_bad = json.loads(f.read())
    return kid_help,kid_bad

def saveKidHelp(kid_help,kid_bad):
    filedate = datetime.now().strftime("%Y_%m_%d")

    with open(f"goals/{filedate}.json", mode='w') as f:
        json.dump([kid_help,kid_bad], f, indent=4)

@app.route('/goals', methods=('GET', 'POST'))
def goals_page():
    user = get_user_from_ip(request.remote_addr)

    kid_help, kid_bad = getKidHelp()

    return render_template('goals.html', uname=user, kid_help=kid_help,kid_bad=kid_bad, cdate=datetime.now().strftime("%A, %m/%d/%Y"))



@app.route('/ticks', methods=('GET', 'POST'))
def ticks_page():
    user = get_user_from_ip(request.remote_addr)

    chores = {}
    check_ticks()
    day_of_year = datetime.now().timetuple().tm_yday
    shift=day_of_year%len(kid_names)
    for i, kid in enumerate(kid_names):
        chores[kid] = chores_list[(i+shift)%5]

    dow = datetime.now().weekday()+2
    if dow==7: dow=0 # M - 2, Sun - 8
    if dow==8: dow=1
    bedtime={}

    totals = summarize_ticks()
    for kid in kid_names:
        ticks = totals[kid][dow]
        if ticks is None or ticks=='': bedtime[kid]=datetime(2025,1,1,9,0,0).strftime("%H:%M PM")
        else: bedtime[kid] = (datetime(2025,1,1,9,0,0)-ticks*timedelta(minutes=10)).strftime("%H:%M PM")

    return render_template('ticks.html', uname=user, data=tick_info, bedtime=bedtime, cdate=datetime.now().strftime("%A, %m/%d/%Y"),chores=chores,totals=totals)

@app.route('/verify', methods=('GET', 'POST'))
def verify():
    check_ticks()
    data = request.get_json()
    name = str(data['name'])
    tick_info[name]['Verified'] = True
    save_ticks()
    return {}


@app.route('/toggle_help', methods=('GET', 'POST'))
def toggle_help():
    data = request.get_json()
    help = str(data['measure'])
    user = str(data['user'])
    kid_help,kid_bad = getKidHelp()
    kid_help[user][help] = data['done']
    saveKidHelp(kid_help,kid_bad)

    return {}

@app.route('/toggle_bad', methods=('GET', 'POST'))
def toggle_bad():
    data = request.get_json()
    bad = str(data['measure'])
    user = str(data['user'])
    kid_help,kid_bad = getKidHelp()
    kid_bad[user][bad] = data['done']
    saveKidHelp(kid_help,kid_bad)

    return {}


@app.route('/toggle', methods=('GET', 'POST'))
def toggle():
    data = request.get_json()
    measure = str(data['measure'])
    check_ticks()
    if 'user' not in data or not data['user']:
        user = get_user_from_ip(request.remote_addr)
        tick_info[user][measure] = data['done']
    else:
        name = data['user']
        tick_info[name][measure] = data['done']
    save_ticks()
    return {}

@app.route('/updateMeasure', methods=('GET', 'POST'))
def updateMeasure():
    check_ticks()
    data = request.get_json()
    name = str(data['name'])
    measure = str(data['measure'])
    tick_info[name][measure]+=data['amt']
    save_ticks()
    return {'updated':True,'count':tick_info[name][measure]}

@app.route('/games', methods=('GET', 'POST'))
def games_page():
    query = request.args.get('q')  # Get the 'q' parameter
    if query is not None and query!='All':
        if query=='Requested':
            filtered_games = sorted([g for g in games if g['requests']>0],key = lambda x:(-x['requests'],x['name']))
        elif len(query)==0:
            filtered_games = [g for g in games if g['name'][0].isnumeric()]
        else:
            filtered_games = [g for g in games if g['name'][0] == query]
    else:
        filtered_games = games
    return render_template('games.html', games=filtered_games, filters=all_letters, is_lh = request.remote_addr=='127.0.0.1')

@app.route('/calendar', methods=('GET', 'POST'))
def calendar():
    return render_template('calendar.html')


@app.route('/submitquestions', methods=('GET', 'POST'))
def submitquestions():
    data = request.get_json()
    question_set = str(data['question_set'])
    wrong_answers = data['wrong']
    wrong_answers.sort(key=lambda item: item['question'])
    numwrong = len(wrong_answers)

    user = get_user_from_ip(request.remote_addr)

    if user not in question_timer:
        print("Start time not saved for "+user)
        return
    question_timer[user]["end_time"] = datetime.now()

    td = question_timer[user]["end_time"]-question_timer[user]["start_time"]

    total_seconds = int(td.total_seconds())

    # Extract hours, minutes, and seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Format as HH:MM:SS with leading zeros
    formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    grade = question_set.split("_")[-1]
    res = {"id": str(uuid.uuid4()) + "_" + grade, "user": user, "score": formatted_time, "grade": grade,"num_wrong":numwrong}

    response_entry = {"ip":request.remote_addr, "user":user, "time":formatted_time,"num_wrong":numwrong,"incorrect":wrong_answers}
    with open("review_questions/"+question_set+".txt", mode='a') as outfile:
        outfile.write(json.dumps(response_entry)+"\n")

    leaderboard[question_set.split("_")[0].capitalize()].append(res)
    leaderboard[question_set.split("_")[0].capitalize()].sort(key=lambda item: (item['num_wrong'], item['score']))

    with open('leaderboard.json', 'w') as f:
        json.dump(leaderboard, f, indent=4)


    return {"data":leaderboard[question_set.split("_")[0].capitalize()],"leader_id":res['id']}


@app.route('/getquestions', methods=('GET', 'POST'))
def getquestions():
    data = request.get_json()
    question_set = str(data['question_set'])

    user = get_user_from_ip(request.remote_addr)

    question_timer[user] = {"quest_set":question_set,"start_time":datetime.now()}
    if question_set=='multiplication_3rd':
        return {"questions":generateTimesTable()}

    return {"questions":[{
            "question": "What is your preferred mode of transportation for commuting?",
            "type": "multiple_choice",
            "options": ["Car", "Public Transit", "Bicycle", "Walk"],
            "id": "q1"
        }]}

@app.route('/requestplay', methods=('GET', 'POST'))
def requestplay():
    data = request.get_json()
    game_id = str(data['game_id'])
    user = get_user_from_ip(request.remote_addr)
    if user not in user_game_requests:
        user_game_requests[user]=[]
    if game_id not in user_game_requests[user]:
        user_game_requests[user].append(game_id)
        count = 0
        for game in games:
            if game['id'] == game_id:
                game['requests']+=1
                count = game['requests']
        with open('play_requests.json', 'w') as f:
            json.dump(user_game_requests, f, indent=4)
        return jsonify({"added":True, "id":game_id, 'count':count})
    else:
        return jsonify({"added":False})

@app.route('/playedgame', methods=('GET', 'POST'))
def playedgame():
    data = request.get_json()
    game_id = str(data['game_id'])
    if request.remote_addr=="127.0.0.1":
        for user, list in user_game_requests.items():
            try:
                list.remove(game_id)
            except:
                pass # doesn't exist in user's request
        with open('play_requests.json', 'w') as f:
            json.dump(user_game_requests, f, indent=4)
        for game in games:
            if game_id == str(game['id']):
                game['requests']=0
        return jsonify({"removed":True, "id":game_id})
    else:
        return jsonify({"removed":False})

@app.route('/requestwatch', methods=('GET', 'POST'))
def requestwatch():
    data = request.get_json()
    movie_id = str(data['movie_id'])
    user = get_user_from_ip(request.remote_addr)

    if user not in user_movie_requests:
        user_movie_requests[user]=[]
    if movie_id not in user_movie_requests[user]:
        user_movie_requests[user].append(movie_id)
        count = 0
        for movie in movies:
            if movie['id'] == movie_id:
                movie['requests']+=1
                count = movie['requests']
        with open('watch_requests.json', 'w') as f:
            json.dump(user_movie_requests, f, indent=4)
        return jsonify({"added":True, "id":movie_id, 'count':count})
    else:
        return jsonify({"added":False})

@app.route('/help', methods=('GET', 'POST'))
def help():
    user = get_user_from_ip(request.remote_addr)
    notification = Notify()
    notification.title = str(user)+" Needs Help"
    notification.message = "Some one has a question."
    notification.icon = "static/images/raise_hand.png"
    notification.send()
    return "Help Request Sent"

@app.route('/')
def index():
    music_files = [song[:-4] for song in os.listdir("static/songs")]
    music_files.sort()
    return render_template('index.html', music_files=music_files)

if __name__ == "__main__":
    ## gunicorn command (uses gunicorn.conf.py):
    # gunicorn flask_plugin_server:app
    # cert_folder = Path(config["cert_folder"])
    #
    # ssl_protocol = ssl.PROTOCOL_TLS_SERVER
    #
    # ctx = ssl.SSLContext(ssl_protocol)

    ## needed if .pem files are encrypted
    #     with open(cert_folder/".cert.pwd", "r") as f:
    #         ctx.load_cert_chain(cert_folder/'cert.pem', cert_folder/'key.pem', password=f.read().rstrip())

    # ctx.load_cert_chain(cert_folder / 'cert.pem', cert_folder / 'key.pem')

    app.run(port=6543,
            host='0.0.0.0'
            # ,ssl_context=ctx
            )
