import datetime
import random

from flask import Flask, jsonify, render_template, request, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "455a109114f26693336cfc320dc74ab0"
db = SQLAlchemy(app)


RESPONSES = {
    "created": {
        "status": "created",
        "msg": "JustAwait created! 😁",
        "detail": "Now just await!",
    },
    "await": {
        "status": "await",
        "msg": "Your await is NOT over! 😒",
        "detail": "Just Await!",
    },
    "over": {
        "status": "over",
        "msg": "Your await IS OVER! 😀",
        "detail": "",
    },
}


class User(db.Model):

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    justawaits = db.relationship("JustAwait", backref="user", lazy=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


class JustAwait(db.Model):

    __tablename__ = "justawait"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    start = db.Column(db.DateTime)
    end = db.Column(db.DateTime)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


class CheckLog(db.Model):

    __tablename__ = "checklog"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User", backref="checklogs", lazy=True)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.id})"


def get_or_create_user(user_id):
    u = db.session.query(User).filter_by(id=user_id).first()
    if u is None:
        u = User(id=user_id)
        db.session.add(u)
        db.session.commit()
    return u


def get_random_delta():
    delta = datetime.timedelta(
        days=random.randint(0, 2),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return delta


def get_justawait(user):
    utcnow = datetime.datetime.utcnow()
    delta = get_random_delta()
    ja = JustAwait(
        user=user,
        start=utcnow,
        end=utcnow + delta,
    )
    return ja


def check_justawait_is_over(user_id):
    last_justawait = db.session\
        .query(JustAwait)\
        .filter(JustAwait.user_id == user_id)\
        .order_by(JustAwait.end.desc())\
        .first()
    if last_justawait is None:
        return True
    log_check_justawait(user_id)
    return datetime.datetime.utcnow() > last_justawait.end


def log_check_justawait(user_id):
    checklog = CheckLog(user_id=user_id)
    db.session.add(checklog)
    db.session.commit()


def get_user_id():
    user_id = session.get("id", None)
    if user_id is None:
        user = User()
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        session["id"] = user_id
    return user_id


@app.route("/")
def home():
    user_id = get_user_id()
    return render_template(
        "home.html",
        title="Home",
    )


@app.route("/justawait", methods=["GET", "POST"])
def justawait():
    user_id = get_user_id()
    user = get_or_create_user(user_id=user_id)
    is_over = check_justawait_is_over(user_id)
    if request.method == "POST" and is_over:
        ja = get_justawait(user)
        db.session.add(ja)
        db.session.commit()
        return jsonify({
            "status": "created",
            "msg": "JustAwait created! 😁",
            "detail": "Now just await!",
        })
    end = [ja.end for ja in user.justawaits][-1].strftime("%Y-%m-%d %H:%M:%S")
    n_checks = len(user.checklogs)
    info = f"Await until {end} | I have made {n_checks} checks"
    if not is_over:
        return jsonify({
            "status": "await",
            "msg": "Your await is NOT over! 😒",
            "detail": "Just Await!",
            "info": info,
        })
    return jsonify({
        "status": "over",
        "msg": "Your await IS OVER! 😀",
        "detail": "",
        "info": info,
    })


@app.route("/about")
def about():
    return render_template("about.html", title="About")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
