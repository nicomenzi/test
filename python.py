import MySQLdb
from sqlalchemy import create_engine, Column, Integer, String, DateTime, TIMESTAMP, text, desc, asc, or_, Table, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, relationship
from datetime import date
from flask import Flask, render_template, request, make_response, session, redirect, g, url_for, flash
from markupsafe import escape
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user,current_user


app = Flask(__name__)
app.secret_key = "Irgend Was Sicheres 12234"


engine = create_engine("mysql+mysqldb://root:admin@localhost:3306/EM", echo=True)
Model = declarative_base()
sql_session = sessionmaker(bind=engine)
sql_session = sql_session()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# gametabelle
class game(Model):

    __tablename__ = "game"

    game_id = Column(Integer, primary_key=True)
    team_Home = Column(Integer, ForeignKey("Team.team_id"))
    team_Away = Column(Integer, ForeignKey("Team.team_id"))
    endstand = Column(String(255))
    pausenstand = Column(String(255))
    goal_player = relationship("goal_player", backref="game_goal")
    team_away = relationship("Team", foreign_keys=[team_Home])
    team_home = relationship("Team", foreign_keys=[team_Away])


# team tabelle
class Team(Model):

    __tablename__ = "Team"

    team_id = Column(Integer, primary_key=True)
    teamname = Column(String(255))
    game_count = Column(String(255))

    player = relationship("player", backref="team")

# player tabelle
class player(Model):

    __tablename__ = "player"

    player_id = Column(Integer, primary_key=True)
    team_idfs = Column(Integer, ForeignKey("Team.team_id"))
    count_goals = Column(Integer)
    name = Column(String(255))
    goal_player = relationship("goal_player", backref="player_goal")

# goal_typ tabelle
class goal_type(Model):

    __tablename__ = "goal_type"
    id = Column(Integer, primary_key=True)
    goal_type = Column(String(255))
    goal_player = relationship("goal_player", backref="goal")
# goal_player zwischentabelle
class goal_player(Model):

     __tablename__ = "goal_player"

     id = Column(Integer, primary_key=True)
     game_idfs = Column(Integer, ForeignKey("game.game_id"))
     time_min_goal = Column(Integer)
     halbzeit = Column(Integer)
     player_idfs = Column(Integer, ForeignKey("player.player_id"))
     goal_idfs = Column(Integer, ForeignKey("goal_type.id"))
# class für dei user login db tabelle
class Login(UserMixin, Model):

    __tablename__ = "login"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    rights  = Column(String(255))
    password = Column(String(255))
# ist für das login zuständig
@login_manager.user_loader
def load_user(user_id):
    try:
        return sql_session.query(Login).get(int(user_id))
    except:
        print("Das hat nicht Funktioniert")

# rendert die home seite
@app.route("/")
def home():
    if "logged_in" not in session:
        session["logged_in"] = False

    session["last_site"] = "home"
    schweiz = sql_session.query(Team).filter_by(teamname="Schweiz").first()
    print(schweiz.player[0].name)


    return render_template("home.html")
# rendert die teams seite
@app.route("/teams/")
def teams():
    session["last_site"] = "teams"
    print('')
    return render_template("teams.html")

# rendert ddie timeline
@app.route("/teams/timeline/<team>")
def timeline(team):
    resultate = []

    games = sql_session.query(game).filter(or_(game.team_Away == team, game.team_Home == team))
    #games_away = sql_session.quer(game).filter_by(or_(teamname=team))
    i = 0
    # erstellt den datensatz für dei seite
    for match in games:
        i = i + 1
        zwischen = {"home" : match.team_home.teamname, "away" : match.team_away.teamname, "result" : match.endstand}
        print(zwischen)
        resultate.append(zwischen)
        # !test!



    print(resultate)
    return render_template("timeline.html", games=games, resultate=resultate )
# rendert die seite für ein neues game hinzufügen
@app.route("/add_game/")
@login_required
def add_game():
    # überprüfen ob der aktuelle benutzer die rechte hat
    if current_user.rights != "admin":
        return redirect(url_for("home"))
    else:
        session["last_site"] = "add_game"
        print("hello fynn")
        teams = sql_session.query(Team).all()
        return render_template("add_game.html", teams=teams)

# rendert das bearbeiten formular
@app.route("/edit_game/<id>/")
@login_required
def edit_game(id ):
    # überprüfen ob der aktuelle benutzer die rechte hat
    if current_user.rights != "admin":
        return redirect(url_for("home"))
    else:
        session["last_site"] = "edit_record"

#       Der datensatz der beartbeitet werden soll wird ausgesucht
        game_data = sql_session.query(game).filter(game.game_id == id).all()

        print(game_data[0].team_away)

        return render_template('edit_game.html', game=game_data)
# datensatz löschen
@app.route("/delete/<id>")
@login_required
def delete(id):
    # überprüfen ob der aktuelle benutzer die rechte hat
    if current_user.rights != "admin":
        return redirect(url_for("home"))
    else:

        # der ausgewählte datensatz wird gelöscht
        sql_session.query(game).filter(game.game_id == id).delete(synchronize_session="fetch")
        sql_session.commit()
        flash('Benutzer gelöscht', "warning")
        return home()
# route um einen datensatz zu bearbeiten
@app.route('/update/', methods=['POST', 'GET'])
def update():
    # Daten werden aus dem Formular ausgelesen
    heimteam = request.form['heimteam']
    auswärtsteam = request.form['auswärtsteam']
    endstand = request.form["endstand"]
    pausenstand = request.form["pausenstand"]
    game_id = request.form["ID"]

    # neue daten werden dem Datensatz hinzugefügt
    sql_session.query(game).filter(game.game_id == game_id).update({game.team_Home: heimteam, game.team_Away: auswärtsteam, game.endstand: endstand, game.pausenstand: pausenstand}, synchronize_session=False)
    sql_session.commit()

    # je nach dem von welcher seite man kommt wird man auf diese seite wieder zurückgeleitet
    return home()
# einen Datensatz hinzufügen
@app.route("/insert/", methods=['POST'])
@login_required
def insert():
    # überprüfen ob der aktuelle benutzer die rechte hat
    if current_user.rights != "admin":
        return redirect(url_for("home"))
    else:
        print(request.form['home_team'])
        print(request.form['away_team'])
        # Dies daten werden aus dem formular ausgelesen
        team_home = request.form['home_team']
        team_away = request.form['away_team']
        endstand = request.form["endstand"]
        pausenstand = request.form["pausenstand"]


        # ein neues spiel  wird hinzugefügt
        new_game = game(team_Home=str(team_home), team_Away=str(team_away), endstand=str(endstand), pausenstand=str(pausenstand) )
        sql_session.add(new_game)
        sql_session.flush()
        sql_session.commit()
        print("xx")
        print(new_game)
        print("xxx")
        flash('Benutzer erfolgreich erstellt', "sucess")
        return home()

# rendert das login template
@app.route("/login/",methods=["GET", "POST"])
def login():
    return render_template("login.html", )

# route um sich einzuloggen
@app.route("/logged_in/",methods=["GET", "POST"])
def logged_in():
    try:
        print("user_login")
        email = request.form["email"]
        password = request.form["password"]
        # wählt den Datensatz
        user = sql_session.query(Login).filter(Login.email == email).first()
        print("user")
        print(user)

        if user:
            # überprüfen ob das eingegebene passwort mit dem pw aus der db übereinstimmt
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                flash('You were successfully logged in', "sucess")
                session["logged_in"] = True

                return redirect(url_for("home"))
            else:
                return redirect(url_for("login"))
    except:

        print()
        flash("Falsches Passwort oder Email", "error")
        return redirect(url_for("home"))


@app.route("/signup/")
def signup():
    return render_template("signup.html")

# erstellt einen neuen benutzer
@app.route("/create_user/", methods=["GET", "POST"])
def create_user():

    # Nimmt dei Daten aus dem FOrmular
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    # Generiert ein gehaschdes passwort
    hashed_password = generate_password_hash(password, method="sha512")
    new_user = Login(username=username, email=email, password=hashed_password )

    # sql_session.add(new_user)
    # sql_session.flush()
    # sql_session.commit()
    # flash('Benutzer erfolgreich erstellt')


    try:
        sql_session.add(new_user)
        sql_session.flush()
        sql_session.commit()
        flash('Benutzer erfolgreich erstellt', "sucess")
        return redirect(url_for("home"))
    except:
        sql_session.rollback()
        flash("Diesen Benutzer gibt es schon", "error")
        return render_template("signup.html")

# Loggt den user aus
@app.route("/logout/")
def logout():
    logout_user()
    session["logged_in"] = False

    return redirect(url_for(session["last_site"]))

# App route für das Admin dashboard
@app.route("/dashboard/")
@login_required
def dashboard():
    # Wenn der aktuelle user nicht die Admin rechte besitzt die adminrechte habe ich in der Datenbank gespeichert
    if current_user.rights != "admin":
        return redirect(url_for("home"))
    else:
    # Gibt dei Tabellen für das Admin Dashboard
        logins = sql_session.query(Login).all()
        teams = sql_session.query(Team).all()
        games = sql_session.query(game).all()
        players = sql_session.query(player).all()

        print(logins)

        return render_template("dashboard.html", logins = logins, teams=teams, games=games, players=players)




if __name__ == "__main__":
    app.run(debug=True)

test