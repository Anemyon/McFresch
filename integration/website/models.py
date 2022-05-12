from os import link
from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    


class User(db.Model, UserMixin):
    __tablename__ = 'User'

    id          = db.Column(db.Integer, primary_key=True)
    vorname     = db.Column(db.String(150))
    name        = db.Column(db.String(150))
    mail        = db.Column(db.String(150), unique=True)
    password    = db.Column(db.String(150))
    premium     = db.Column(db.Integer)
    vegan       = db.Column(db.Integer)
    week1       = db.Column(db.Integer)
    week2       = db.Column(db.Integer)
    week3       = db.Column(db.Integer)
    week4       = db.Column(db.Integer)
    week5       = db.Column(db.Integer)
    
    #notes = db.relationship('Note')

class Dishes(db.Model):
    __tablename__ = 'Dishes'

    dishID       = db.Column(db.Integer, primary_key=True)
    link            = db.Column(db.String(120))
    duration       = db.Column(db.Integer)
    difficulty   = db.Column(db.Integer)
    milkproducts    = db.Column(db.Integer)
    meatproducts  = db.Column(db.Integer)
    fishproducts    = db.Column(db.Integer)
    roughage    = db.Column(db.Integer)
    fruits            = db.Column(db.Integer)
    vegetable         = db.Column(db.Integer)
    oil            = db.Column(db.Integer)
    sweet           = db.Column(db.Integer)
    kitchen          = db.Column(db.Integer)
    img             = db.Column(db.String(300), unique = True)

    
class Rating(db.Model):
    __tablename__ = 'Rating'

    ratingID  	    = db.Column(db.Integer, primary_key=True)
    userID          = db.Column(db.Integer)
    dishID       = db.Column(db.Integer)
    datum           = db.Column(db.String(120))
    rating          = db.Column(db.Integer)

    