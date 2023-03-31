from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

from env import SECRET_KEY, API_KEY

MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movie-cllection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(250), unique=True, nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(80))
    imgUrl = db.Column(db.String(100), unique=True, nullable=False)

with app.app_context():
    db.create_all()

class AddForm(FlaskForm):
    title = StringField(label="Movie Title")
    done = SubmitField(label="Add movie")

class EditForm(FlaskForm):
    rating = StringField(label="Your rating out of 10 e.g. 7,5")
    review = StringField(label="Your review")
    done = SubmitField(label="Done")


@app.route("/")
def home():
    movieList = Movie.query.order_by(Movie.rating).all()
    for i in range(len(movieList)):
        movieList[i].ranking = len(movieList) - i
    db.session.commit()
    return render_template("index.html", movies=movieList)

@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        movieTitle = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key":API_KEY, "query": movieTitle})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)

@app.route("/find")
def find():
    movieApiId = request.args.get("id")
    if movieApiId:
        movieApiUrl = f"{MOVIE_DB_INFO_URL}/{movieApiId}"
        response = requests.get(movieApiUrl, params={"api_key":API_KEY})
        data = response.json()        
        newMovie = Movie(
            title = data["title"],
            year = data["release_date"].split("-")[0],
            imgUrl = f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description = data["overview"],
        )
        db.session.add(newMovie)
        db.session.commit()
        return redirect(url_for("edit", id=newMovie.id))

@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()
    movieId = request.args.get("id")
    movie = Movie.query.get(movieId)
    if form.validate_on_submit():
        with app.app_context():
            movie.rating = float(form.rating.data)
            movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete")
def delete():
    movieId = request.args.get("id")
    movie = Movie.query.get(movieId)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)