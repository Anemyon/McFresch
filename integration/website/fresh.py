from re import X
from defusedxml import DTDForbidden
import mysql.connector
import pandas as pd
import sklearn as sk
from sklearn.linear_model import LogisticRegression
import os
import json
from datetime import date
import datetime
import numpy as np
import joblib
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
import sklearn.model_selection
import sklearn.metrics
import sklearn.neural_network
import random
from bs4 import BeautifulSoup
import requests
import re
from  sqlalchemy.sql.expression import func, select
import sqlalchemy
import os
from datetime import date, datetime
import sqlite3
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from sqlalchemy import null, true
from .models import User,Dishes,Rating
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from werkzeug.utils import secure_filename
from flask_login import login_user, login_required, logout_user, current_user


from collections import defaultdict

from sqlalchemy import create_engine
from sqlalchemy.inspection import inspect
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

fresh = Blueprint('fresh', __name__)

#function is used, to convert the database entries into pandas df for ai
def query_to_dict(rset):
    result = defaultdict(list)
    for obj in rset:
        instance = inspect(obj)
        for key, x in instance.attrs.items():
            result[key].append(x.value)
    return result

#converts the dict in which ingredients are saved to a nested list, for visualisation later on
def ingr_to_string(dict_ingr) :
    new_List = []
    for key in dict_ingr:
            new_List.append(dict_ingr[key])


    

    ret_list = []
    i = 0

    while i in range(len(new_List)) :
        singel_combi = []
        singel_combi.append(new_List[i])
        singel_combi.append(new_List[(i+1)])
        ret_list.append(singel_combi)
        i = i + 2

 
    return ret_list

#main and landing page
@fresh.route('/main')
def main () :
    return render_template("main.html")

#is called when user presses big button on main page, checks for authentication
@fresh.route('/makeweek')
def makeweek () :

    if current_user.is_authenticated:
        

        return redirect(url_for('fresh.weekplan'))

    else :
        return render_template("login.html")

#key of the application, creates week view for user
@fresh.route('/weekplan', methods=['GET', 'POST'])
def weekplan () :

    #if a new week is requested by user
    if request.method == "POST" :
        week1       = request.form.get("1")
        week2       = request.form.get("2")
        week3       = request.form.get("3")
        week4       = request.form.get("4")
        week5       = request.form.get("5")

        #get database entries for dishes

        this_week1 = Dishes.query.filter_by(dishID = week1).first()
        this_week2 = Dishes.query.filter_by(dishID = week2).first()
        this_week3 = Dishes.query.filter_by(dishID = week3).first()
        this_week4 = Dishes.query.filter_by(dishID = week4).first()
        this_week5 = Dishes.query.filter_by(dishID = week5).first()

        old_dishes = []
        old_dishes.append(this_week1)
        old_dishes.append(this_week2)
        old_dishes.append(this_week3)
        old_dishes.append(this_week4)
        old_dishes.append(this_week5)

        dishes = []

        #get all relevant data for a swipe
        for entry in old_dishes :

            single_dish = []
            id             = entry.dishID
            img            = entry.img
            link           = entry.link
            name           = getHTMLdocument(link, 1)

            single_dish.append(name)
            single_dish.append(img)
            single_dish.append(id)

            dishes.append(single_dish)

        #update user database 
        user_id = current_user.id

        this_user = User.query.filter_by(id = user_id).first()

        this_user.week1 = None
        this_user.week2 = None
        this_user.week3 = None
        this_user.week4 = None
        this_user.week5 = None

        db.session.commit()


        return render_template("mcswipe.html", dishes=dishes)

    #if the site is accessed in the normal way

    user = current_user.id

    this_user = User.query.filter_by(id=user).first()

    #check if the user has dishes to display, 

    if this_user.week1 == None :

        #if user has no dishes this has to possible reasons
        #1. he has swiped his old ones and is ready for a new ai generated menu
        #2. he left the sign up process and did not performe an initial swipe

        rating = Rating.query.filter_by(userID=user).first()

        #if he has not swiped yet, let him rate dishes so ai can work
        if rating == None:
            dishes = setup_first()

            return render_template("mcswipe.html", dishes=dishes)

        #else he is ready for ai

        single_dish = []

        #calling the ai and creating five dishes
        
        week1,week2,week3,week4,week5 = makeme(user)

        #those dishes get displayed

        new_dishes = []
        new_dishes.append(week1)
        new_dishes.append(week2)
        new_dishes.append(week3)
        new_dishes.append(week4)
        new_dishes.append(week5)

        finale_dishes = []

        #gathering all needed data

        for entry in new_dishes :
            single_dish = []
            this_week = Dishes.query.filter_by(dishID = entry).first()
            img                         = this_week.img
            link                        = this_week.link
            ingr, name                  = getHTMLdocument(link, 0)
            ingr                        = ingr_to_string(ingr)
            prep                        = detailview(link)
            index_e = new_dishes.index(entry) + 1

            single_dish.append(entry)
            single_dish.append(img)
            single_dish.append(name)
            single_dish.append(ingr)
            single_dish.append(prep)
            single_dish.append(index_e)
            finale_dishes.append(single_dish)

            #calculating the suplements the user needs

            sups = calculatedefizit(user)

        return render_template("weekplan.html", dishes = finale_dishes, sups = sups )
    else:

        #if he has dishes set, he is just casually viewing his menu
        #same process as above, could have been an additional function to minimize loc

        new_dishes = []

        week1      = this_user.week1
        week2      = this_user.week2
        week3      = this_user.week3
        week4      = this_user.week4
        week5      = this_user.week5

        finale_dishes = []

        new_dishes.append(week1)
        new_dishes.append(week2)
        new_dishes.append(week3)
        new_dishes.append(week4)
        new_dishes.append(week5)

        for entry in new_dishes :
            single_dish = []
            this_week = Dishes.query.filter_by(dishID = entry).first()
            img                         = this_week.img
            link                        = this_week.link
            ingr, name                  = getHTMLdocument(link, 0)
            ingr                        = ingr_to_string(ingr)
            prep                        = detailview(link)
            index_e = new_dishes.index(entry) + 1

            single_dish.append(entry)
            single_dish.append(img)
            single_dish.append(name)
            single_dish.append(ingr)
            single_dish.append(prep)
            single_dish.append(index_e)
            finale_dishes.append(single_dish)
        
            sups = calculatedefizit(user)

        return render_template("weekplan.html", dishes = finale_dishes, sups = sups )

@fresh.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('fresh.login'))

#used to initially create db, no function, would be deleted if released
@fresh.route('/createdishes')
def createdishes():


    dishID       = 0
    link            = "https://www.chefkoch.de/rezepte/2483121390658464/Spaghetti-Bolognese-als-Babybrei.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 0
    img             = "IMG.0.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 1
    link            = "https://www.chefkoch.de/rezepte/742751176880700/Agis-Gyros-in-Metaxasauce.html"
    duration       = 70
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.1.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 2
    link            = "https://www.chefkoch.de/rezepte/262751102375096/Griechischer-Bauernsalat.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.2.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 3
    link            = "https://www.chefkoch.de/rezepte/182641078820881/Griechische-Haehnchenpfanne.html"
    duration       = 100
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.3.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 4
    link            = "https://www.chefkoch.de/rezepte/1045251209462585/Moussaka.html"
    duration       = 170
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.4.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 5
    link            = "https://www.chefkoch.de/rezepte/632811163949927/Gebackener-Schafskaese.html"
    duration       = 10
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.5.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 6
    link            = "https://www.chefkoch.de/rezepte/3138791467380733/Griechische-Meze-Flambierte-Garnelen.html"
    duration       = 35
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 4
    img             = "IMG.6.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 7
    link            = "https://www.chefkoch.de/rezepte/2356341374556671/Griechische-dicke-weisse-Bohnen-in-Tomatensosse.html"
    duration       = 225
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.7.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 8
    link            = "https://www.chefkoch.de/rezepte/2318071369564257/Griechischer-Tomatensalat-a-la-Dimitrios.html"
    duration       = 135
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.8.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 9
    link            = "https://www.chefkoch.de/rezepte/1946901316786698/Koestliches-Zitronenhaehnchen.html"
    duration       = 80
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 1
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.9.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 10
    link            = "https://www.chefkoch.de/rezepte/1802261291329637/botos-Bifteki-mit-griechischem-Tomatenreis.html"
    duration       = 45
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.10.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 11
    link            = "https://www.chefkoch.de/rezepte/1621071269341260/Spitzpaprika-Schiffchen.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 4
    img             = "IMG.11.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 12
    link            = "https://www.chefkoch.de/rezepte/2605011409315392/Griechische-Schweinerouladen-in-Metaxa-Sahne-Sosse.html"
    duration       = 75
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 4
    img             = "IMG.12.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 13
    link            = "https://www.chefkoch.de/rezepte/2090601337673029/Gegrillte-Rinderleber-a-la-Duchemin.html"
    duration       = 78
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.13.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 14
    link            = "https://www.chefkoch.de/rezepte/1282351233648069/Griechischer-Hackauflauf-mit-Kritharaki-Nudeln.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.14.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 15
    link            = "https://www.chefkoch.de/rezepte/1048301209719211/Galaktoboureko-griechischer-Griessauflauf.html"
    duration       = 80
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 0
    oil            = 0
    sweet           = 1
    kitchen          = 4
    img             = "IMG.15.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 16
    link            = "https://www.chefkoch.de/rezepte/88111034501599/Lamm-aus-dem-Ofen.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.16.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 17
    link            = "https://www.chefkoch.de/rezepte/567611155305211/Lamm-Stifado-mit-Kritharaki.html"
    duration       = 140
    difficulty   = 2
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.17.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 18
    link            = "https://www.chefkoch.de/rezepte/1848481299504900/Kreta-Feldsalat-mit-Schafskaese.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.18.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 19
    link            = "https://www.chefkoch.de/rezepte/328211115381002/Galaktobouriko.html"
    duration       = 40
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 0
    oil            = 0
    sweet           = 1
    kitchen          = 4
    img             = "IMG.19.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 20
    link            = "https://www.chefkoch.de/rezepte/2919831444263376/Kritharaki-Felixos.html"
    duration       = 25
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 4
    img             = "IMG.20.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 21
    link            = "https://www.chefkoch.de/rezepte/2529901396468055/Huhn-mit-Backpflaumen-Honig-und-Zimt.html"
    duration       = 60
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 0
    oil            = 0
    sweet           = 1
    kitchen          = 5
    img             = "IMG.21.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 22
    link            = "https://www.chefkoch.de/rezepte/628611163332620/Afrikanischer-Erdnusseintopf.html"
    duration       = 45
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.22.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 23
    link            = "https://www.chefkoch.de/rezepte/1324581237330785/Cape-Town-Chicken-Curry.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.23.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 24
    link            = "https://www.chefkoch.de/rezepte/2018261326965478/Couscoussalat-mit-Rosinen-und-Minze.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.24.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 25
    link            = "https://www.chefkoch.de/rezepte/2418781381833932/Vegetarisches-Mafe.html"
    duration       = 50
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.25.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 26
    link            = "https://www.chefkoch.de/rezepte/2674771419966379/Domoda.html"
    duration       = 75
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.26.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 27
    link            = "https://www.chefkoch.de/rezepte/4071131635316982/Hirsch-Tajine-mit-Kichererbsen-und-Backpflaumen.html"
    duration       = 240
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 5
    img             = "IMG.27.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 28
    link            = "https://www.chefkoch.de/rezepte/1546701261146497/Marokkanisches-Rindsragout-mit-Okraschoten.html"
    duration       = 35
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.28.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 29
    link            = "https://www.chefkoch.de/rezepte/1498471255333864/Falafel-aus-rohen-Kichererbsen.html"
    duration       = 40
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.29.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 30
    link            = "https://www.chefkoch.de/rezepte/1972611320337623/Marokkanischer-vegetableeintopf-mit-Huelsenfruechten.html"
    duration       = 50
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.30.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 31
    link            = "https://www.chefkoch.de/rezepte/3421871509745935/Huehnchen-mit-Kichererbsen-in-Tomaten-aus-der-Tajine.html"
    duration       = 135
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 5
    img             = "IMG.31.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 32
    link            = "https://www.chefkoch.de/rezepte/1256581231148160/Afrikanische-Kokosforellen-mit-Ingwer.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.32.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 33
    link            = "https://www.chefkoch.de/rezepte/1143421220702285/Scharfer-Butternut-Kuerbis.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.33.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 34
    link            = "https://www.chefkoch.de/rezepte/506631145837800/Couscous-Salat-a-la-Foe.html"
    duration       = 150
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.34.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 35
    link            = "https://www.chefkoch.de/rezepte/1983621321645997/Marokkanischer-Shepherds-Pie.html"
    duration       = 60
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.35.jpg"	

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()



    dishID       = 36
    link            = "https://www.chefkoch.de/rezepte/3347651497529252/Afrikanisches-Stew.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 5
    img             = "IMG.36.jpg"	

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 37
    link            = "https://www.chefkoch.de/rezepte/3108011463677136/Marokkanisches-Huehnchen-mit-Blumenkohl.html"
    duration       = 85
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.37.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 38
    link            = "https://www.chefkoch.de/rezepte/1330241237886706/Orientalisch-gefuellter-Kuerbis.html"
    duration       = 85
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.38.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 39
    link            = "https://www.chefkoch.de/rezepte/715571174315059/Lachs-auf-Spinat-Couscous.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.39.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 40
    link            = "https://www.chefkoch.de/rezepte/507981146060087/Fischsuppe.html"
    duration       = 40
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 5
    img             = "IMG.40.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 41
    link            = "https://www.chefkoch.de/rezepte/2133281343053838/Rinderrouladen-klassisch.html"
    duration       = 180
    difficulty   = 2
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.41.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 42
    link            = "https://www.chefkoch.de/rezepte/1998981323763212/Koenigsberger-Klopse.html"
    duration       = 85
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.42.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 43
    link            = "https://www.chefkoch.de/rezepte/1594161266675503/Erbseneintopf-nach-Bundeswehrrezept.html"
    duration       = 95
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.43.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 44
    link            = "https://www.chefkoch.de/rezepte/1243811229272585/Schwaebischer-Zwiebelkuchen.html"
    duration       = 205
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.44.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 45
    link            = "https://www.chefkoch.de/rezepte/1583701265817692/Krustenbraten.html"
    duration       = 165
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.45.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 46
    link            = "https://www.chefkoch.de/rezepte/1748901284210089/Dicke-fruits-Pfannkuchen.html"
    duration       = 40
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 1
    vegetable         = 0
    oil            = 0
    sweet           = 1
    kitchen          = 1
    img             = "IMG.46.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 47
    link            = "https://www.chefkoch.de/rezepte/1415521246449438/Berliner-Kartoffelsuppe.html"
    duration       = 50
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.47.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 48
    link            = "https://www.chefkoch.de/rezepte/210591088150766/Soljanka-nach-Mama-Art.html"
    duration       = 75
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.48.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 49
    link            = "https://www.chefkoch.de/rezepte/1460441251004217/Kaesespaetzle-mit-Lachs-und-Shrimps-Auflauf.html"
    duration       = 45
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.49.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 50
    link            = "https://www.chefkoch.de/rezepte/1323281237244433/Omas-Pannfisch.html"
    duration       = 85
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 1
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.50.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 51
    link            = "https://www.chefkoch.de/rezepte/1034171208527833/Marions-Spaghetti-Speciale.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.51.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 52
    link            = "https://www.chefkoch.de/rezepte/431091134310048/Gulasch-nach-Oma-Magda.html"
    duration       = 160
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.52.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 53
    link            = "https://www.chefkoch.de/rezepte/426431133556910/Omas-Kohlrouladen.html"
    duration       = 90
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.53.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 54
    link            = "https://www.chefkoch.de/rezepte/1948521317045172/Tafelspitz-mit-Meerrettichsosse.html"
    duration       = 180
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.54.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 55
    link            = "https://www.chefkoch.de/rezepte/1212421227011839/Omas-Endiviensalat.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.55.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 56
    link            = "https://www.chefkoch.de/rezepte/1231931228220006/Omas-echter-Berliner-Kartoffelsalat.html"
    duration       = 310
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.56.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 57
    link            = "https://www.chefkoch.de/rezepte/30491008174307/Kaninchenbraten-Thueringer-Art.html"
    duration       = 310
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 1
    img             = "IMG.57.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()



    dishID       = 58
    link            = "https://www.chefkoch.de/rezepte/1716781280412009/Sauerbraten-mit-Rotkohl-und-Kartoffelkloessen.html"
    duration       = 150
    difficulty   = 2
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 1
    img             = "IMG.58.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 59
    link            = "https://www.chefkoch.de/rezepte/3112261464165182/Leber-nach-Berliner-Art.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 1
    vegetable         = 0
    oil            = 0
    sweet           = 1
    kitchen          = 1
    img             = "IMG.59.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 60
    link            = "https://www.chefkoch.de/rezepte/610191160978023/Kohl-geschmort-mit-Hackfleisch.html"
    duration       = 70
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 1
    img             = "IMG.60.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 61
    link            = "https://www.chefkoch.de/rezepte/2766911428603391/Indisches-Butter-Chicken-aus-dem-Ofen.html"
    duration       = 120
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 2
    img             = "IMG.61.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 62
    link            = "https://www.chefkoch.de/rezepte/2033501329494843/Spitzkohl-Curry.html"
    duration       = 55
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.62.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 63
    link            = "https://www.chefkoch.de/rezepte/1530241258527897/Linsen-Mangold-Curry.html"
    duration       = 35
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.63.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 64
    link            = "https://www.chefkoch.de/rezepte/2801191432230478/Dal-Rote-Linsen.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 2
    img             = "IMG.64.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 65
    link            = "https://www.chefkoch.de/rezepte/2686111421307206/Raffiniertes-Curry-mit-Mango-Kuerbis-und-Cashewkernen.html"
    duration       = 40
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.65.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 66
    link            = "https://www.chefkoch.de/rezepte/4045141625047898/Zwiebel-Bhajis-Indische-Zwiebel-Bratlinge.html"
    duration       = 40
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 2
    img             = "IMG.66.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 67
    link            = "https://www.chefkoch.de/rezepte/3205181477080543/Tandoori-Masala-Chicken-Curry.html"
    duration       = 270
    difficulty   = 2
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.67.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 68
    link            = "https://www.chefkoch.de/rezepte/1430761247928622/Palak-Paneer.html"
    duration       = 175
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 2
    img             = "IMG.68.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 69
    link            = "https://www.chefkoch.de/rezepte/797311183369621/Rotes-Lammcurry.html"
    duration       = 35
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.69.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 70
    link            = "https://www.chefkoch.de/rezepte/3920821598731193/Jackfruit-Curry.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 2
    img             = "IMG.70.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 71
    link            = "https://www.chefkoch.de/rezepte/2549491399130536/Dateberry.html"
    duration       = 75
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 2
    img             = "IMG.71.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 72
    link            = "https://www.chefkoch.de/rezepte/3761631572738144/Indische-Bananenpfanne.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 0
    oil            = 0
    sweet           = 1
    kitchen          = 2
    img             = "IMG.72.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 73 	
    link            = "https://www.chefkoch.de/rezepte/1323671237285440/fruitspfanne.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 1
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 2
    img             = "IMG.73.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 74 	
    link            = "https://www.chefkoch.de/rezepte/217831090831541/Blattspinat-mit-Zwiebeln.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.74.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 75	
    link            = "https://www.chefkoch.de/rezepte/2656431417104774/Indischer-vegetabletopf-mit-Lammhackbaellchen-und-sweetkartoffeln.html"
    duration       = 60
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 2
    img             = "IMG.75.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 76
    link            = "https://www.chefkoch.de/rezepte/1369421241852936/Haehnchen-Ananas-Curry-mit-Kokosmilch.html"
    duration       = 40
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 1
    vegetable         = 0
    oil            = 0
    sweet           = 0
    kitchen          = 2
    img             = "IMG.76.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 77
    link            = "https://www.chefkoch.de/rezepte/1897461309194953/Chicken-Tikka-Masala.html"
    duration       = 45
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.77.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 78
    link            = "https://www.chefkoch.de/rezepte/2512401394277679/Vegetarisches-mildes-Korma.html"
    duration       = 60
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.78.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 79
    link            = "https://www.chefkoch.de/rezepte/1775561287564547/Scharfer-indischer-Salat-mit-Gurken-Tomaten-Erdnuessen-und-Chili.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.79.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 80
    link            = "https://www.chefkoch.de/rezepte/1244181229349167/Zucchini-Pakoras.html"
    duration       = 35
    difficulty   = 2
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 2
    img             = "IMG.80.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 81
    link            = "https://www.chefkoch.de/rezepte/1045691209479240/Mexikanische-Burritos.html"
    duration       = 50
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.81.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 82
    link            = "https://www.chefkoch.de/rezepte/3134211466860185/Gefuellte-Paprika-Mexican-Style.html"
    duration       = 55      
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.82.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 83
    link            = "https://www.chefkoch.de/rezepte/1050121209976105/Chicken-Wrap-mit-vegetable-Guacamole-und-Creme-fraiche.html"
    duration       = 180
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.83.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 84
    link            = "https://www.chefkoch.de/rezepte/3128201466080563/Burritos.html"
    duration       = 70
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.84.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 85
    link            = "https://www.chefkoch.de/rezepte/1069791212561652/Ueberbackene-Enchiladas-mit-Tzatziki.html"
    duration       = 60
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.85.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()



    dishID       = 86
    link            = "https://www.chefkoch.de/rezepte/1958641318570605/Mells-mexikanische-Enchilada-Lasagne.html"
    duration       = 50
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.86.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 87
    link            = "https://www.chefkoch.de/rezepte/267501103161368/Mexikanischer-Schichtsalat.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.87.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 88
    link            = "https://www.chefkoch.de/rezepte/2376151376828764/Tacos-de-Carnitas.html"
    duration       = 180
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 3
    img             = "IMG.88.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 89
    link            = "https://www.chefkoch.de/rezepte/1045891209496959/Shrimps-Papaya-Salat.html"
    duration       = 45
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 0
    fruits            = 1
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 3
    img             = "IMG.89.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()



    dishID       = 90
    link            = "https://www.chefkoch.de/rezepte/225051092820022/Spaghetti-mit-Tomaten-Avocado-Salsa.html"
    duration       = 45
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.90.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()



    dishID       = 91
    link            = "https://www.chefkoch.de/rezepte/268711103449042/Koriander-Thunfischsteak-mit-Mango-Salsa.html"
    duration       = 75
    difficulty   = 2
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 0
    fruits            = 1
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.91.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 92
    link            = "https://www.chefkoch.de/rezepte/438441135895486/Mexikanisches-Reisfleisch.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.92.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()


    dishID       = 93
    link            = "https://www.chefkoch.de/rezepte/3459011515328610/Mexikanisches-Kumpir.html"
    duration       = 70
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.93.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit() 


    dishID       = 94
    link            = "https://www.chefkoch.de/rezepte/797161183359729/Nudelgericht-Wuestensonnenuntergang.html"
    duration       = 25
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.94.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit() 



    dishID       = 95
    link            = "https://www.chefkoch.de/rezepte/496381144199268/Frijolitos.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.95.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit() 


    dishID       = 96
    link            = "https://www.chefkoch.de/rezepte/3322481493373491/Mexikanische-Fruehstuecks-Bratkartoffeln.html"
    duration       = 45
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.96.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit() 


    dishID       = 97
    link            = "https://www.chefkoch.de/rezepte/401721129237465/Vegetarisches-Chili.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.97.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit() 



    dishID       = 98
    link            = "https://www.chefkoch.de/rezepte/1759351285652571/Gegrillte-Quesadillas.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 3
    img             = "IMG.98.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit() 


    dishID       = 99
    link            = "https://www.chefkoch.de/rezepte/281111106232968/Chili-con-Carne.html"
    duration       = 150
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.99.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit() 


    dishID       = 100
    link            = "https://www.chefkoch.de/rezepte/643641165471128/Mexikanischer-Bohnensalat.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 3
    img             = "IMG.100.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 101
    link            = "https://www.chefkoch.de/rezepte/2210881354095272/Pulled-Pork-zarter-Schweinebraten-aus-dem-Ofen-fast-original-nur-ohne-Grill.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 6
    img             = "IMG.101.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 102
    link            = "https://www.chefkoch.de/rezepte/3084171461052354/Knusprige-Chicken-Nuggets-selber-machen.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.102.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 103
    link            = "https://www.chefkoch.de/rezepte/1604241267611123/BBQ-Garnelen-in-Honig-Senf-Sauce.html"
    duration       = 10
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 6
    img             = "IMG.103.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 104
    link            = "https://chefkoch.de/rezepte/2528971396357517/American-Cheeseburger.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.104.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 105
    link            = "https://www.chefkoch.de/rezepte/2220831355433935/Philly-Cheese-Steak-Sandwich.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.105.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 106
    link            = "https://www.chefkoch.de/rezepte/3357251499163032/Pan-Pizza-mit-Kaese-Rand.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.106.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 107
    link            = "https://www.chefkoch.de/rezepte/452791137770019/All-American-Burger.html"
    duration       = 45
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.107.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 108
    link            = "https://www.chefkoch.de/rezepte/3084211461053731/Pumpkin-Patties-wuerzige-Kuerbis-Puffer.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 6
    img             = "IMG.108.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 109
    link            = "https://www.chefkoch.de/rezepte/3080521460722346/Sloppy-Joes-Amerikanische-Hackfleisch-Burger.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.109.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 110
    link            = "https://www.chefkoch.de/rezepte/1729131282039951/Burger-Patties.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.110.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 111
    link            = "https://www.chefkoch.de/rezepte/3084201461053377/Potato-Puffs-mit-Dip-knusprig-cremige-Kartoffelplaetzchen.html"
    duration       = 50
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.111.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 112
    link            = "https://www.chefkoch.de/rezepte/1847311299234839/Killer-Mac-and-Cheese.html"
    duration       = 10
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.112.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 113
    link            = "https://www.chefkoch.de/rezepte/2221071355485152/Geraeucherte-Baconbombe-mit-Kaese-Pilzfuellung.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.113.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 114
    link            = "https://www.chefkoch.de/rezepte/3128221466081669/Chicken-Nuggets-in-Cornflakeskruste-mit-selbstgemachtem-Ketchup.html"
    duration       = 60
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 6
    img             = "IMG.114.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 115
    link            = "https://www.chefkoch.de/rezepte/1679731276069495/Spezial-Spare-Ribs.html"
    duration       = 60
    difficulty   = 2
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 6
    img             = "IMG.115.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 116
    link            = "https://www.chefkoch.de/rezepte/1426751247563051/Spareribs-NT-im-Bratschlauch.html"
    duration       = 60
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 6
    img             = "IMG.116.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 117
    link            = "https://www.chefkoch.de/rezepte/2917341444052986/Pulled-Pork-aus-dem-Ofen.html"
    duration       = 90
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 1
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 6
    img             = "IMG.117.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 118
    link            = "https://www.chefkoch.de/rezepte/3165941471280045/Cheeseburger-Kuchen.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.118.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 119
    link            = "https://www.chefkoch.de/rezepte/3291881488754107/Mediterrane-gebackene-sweetkartoffeln-mit-geroesteten-Kichererbsen.html"
    duration       = 5
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 6
    img             = "IMG.119.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 120
    link            = "https://www.chefkoch.de/rezepte/1638801271408312/Crispy-Fried-Chicken.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 0
    kitchen          = 6
    img             = "IMG.120.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 121
    link            = "https://www.chefkoch.de/rezepte/61751022414158/Thailaendische-Wokpfanne-mit-Kokosmilch.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.121.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 122
    link            = "https://www.chefkoch.de/rezepte/2668971418975818/Gebratene-Mie-Nudeln-mit-Haehnchen.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.122.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 123
    link            = "https://www.chefkoch.de/rezepte/2848091436834550/Chinesisch-gebratene-Nudeln-mit-Huehnchenfleisch-Ei-und-vegetable.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.123.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 124
    link            = "https://www.chefkoch.de/rezepte/3618671544190713/Chicken-Teriyaki-der-japanische-Klassiker.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.124.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 125
    link            = "https://www.chefkoch.de/rezepte/2826671434712499/Haehnchen-sweetsauer-wie-im-Chinarestaurant.html"
    duration       = 25
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 7
    img             = "IMG.125.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 126
    link            = "https://www.chefkoch.de/rezepte/1320181236816286/Wokvegetable-mit-Erdnusssosse-und-Scampi.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.126.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 127
    link            = "https://www.chefkoch.de/rezepte/1841791298475753/Chinesisches-Rindfleisch-mit-Zwiebeln-und-Paprika.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.127.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 128
    link            = "https://www.chefkoch.de/rezepte/2817731433772466/Vietnamesische-Sommerrollen.html"
    duration       = 45
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.128.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 129
    link            = "https://www.chefkoch.de/rezepte/2766911428603391/Indisches-Butter-Chicken-aus-dem-Ofen.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.129.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 130
    link            = "https://www.chefkoch.de/rezepte/2564751401396427/Glasiertes-Huhn-mit-Hoisinsauce-und-Cashewkernen.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.130.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 131
    link            = "https://www.chefkoch.de/rezepte/63051022929691/Gebratene-Nudeln.html"
    duration       = 10
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.131.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 132
    link            = "https://www.chefkoch.de/rezepte/1804951291896974/Thai-Curry-Erdnuss-Kokos-Huehnchen.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.132.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 133
    link            = "https://www.chefkoch.de/rezepte/142961061488437/Gebratenes-Huehnchen-mit-Mie-Nudeln.html"
    duration       = 45
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 7
    img             = "IMG.133.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 134
    link            = "https://www.chefkoch.de/rezepte/910271196192317/Brokkoli-Honig-Haehnchen.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.134.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 135
    link            = "https://www.chefkoch.de/rezepte/1651831272990064/Pikante-Thai-Suppe-mit-Kokos-und-Huehnchen.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 7
    img             = "IMG.135.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 136
    link            = "https://www.chefkoch.de/rezepte/1761961285878272/Nasi-Goreng.html"
    duration       = 15
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.136.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 137
    link            = "https://www.chefkoch.de/rezepte/1804511291817891/Japanische-Nudelsuppe-mit-Huehnerbruehe-und-Schweinefilet-Ramen.html"
    duration       = 45
    difficulty   = 2
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.137.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 138
    link            = "https://www.chefkoch.de/rezepte/1054511210486367/Fruehlingsrollen.html"
    duration       = 45
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 7
    img             = "IMG.138.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 139
    link            = "https://www.chefkoch.de/rezepte/1594721266741395/Gong-Bao-Chicken.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 7
    img             = "IMG.139.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 140
    link            = "https://www.chefkoch.de/rezepte/460771139185700/Schnelles-Thai-Curry-mit-Huhn-Paprika-und-feiner-Erdnussnote.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 7
    img             = "IMG.140.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 141
    link            = "https://www.chefkoch.de/rezepte/4080481638604337/Schwarzwaelder-Pilz-Dim-Sum-mit-Sojasauce.html"
    duration       = 60
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.141.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 142
    link            = "https://www.chefkoch.de/rezepte/4045481625128358/Kichererbsen-Salat.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 8
    img             = "IMG.142.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 143
    link            = "https://www.chefkoch.de/rezepte/914031196710118/Griessbrei-von-Grossmutter.html"
    duration       = 15
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.143.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 144
    link            = "https://www.chefkoch.de/rezepte/2587261406118751/Baguette-magique.html"
    duration       = 5
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 0
    sweet           = 1
    kitchen          = 8
    img             = "IMG.144.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 145
    link            = "https://www.chefkoch.de/rezepte/1900361309694639/Altbaerlis-Kaiserschmarrn.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 8
    img             = "IMG.145.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 146
    link            = "https://www.chefkoch.de/rezepte/1574651265014378/Serviettenknoedel.html"
    duration       = 10
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 8
    img             = "IMG.146.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 147
    link            = "https://www.chefkoch.de/rezepte/1031841208350942/Kaiserschmarrn-Tiroler-Landgasthofrezept.html"
    duration       = 15
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 1
    sweet           = 1
    kitchen          = 8
    img             = "IMG.147.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 148
    link            = "https://www.chefkoch.de/rezepte/2114131340630587/Vegetarische-Spinat-vegetable-Lasagne-mit-Tomatensosse.html"
    duration       = 25
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.148.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 149
    link            = "https://www.chefkoch.de/rezepte/716331174378295/Italienischer-Pizzateig.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 0
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.149.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 150
    link            = "https://www.chefkoch.de/rezepte/3116611464630134/Bulgur-Buddha-Bowl.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0 
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.150.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 151
    link            = "https://www.chefkoch.de/rezepte/3023041455110341/Rote-Linsen-Curry-mit-sweetkartoffeln.html"
    duration       = 10
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 8
    img             = "IMG.151.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 152
    link            = "https://www.chefkoch.de/rezepte/1639971271583788/Ratatouille.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.152.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 153
    link            = "https://www.chefkoch.de/rezepte/3218701478967636/Mango-Linsensalat-mit-mariniertem-Tofu.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.153.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 154
    link            = "https://www.chefkoch.de/rezepte/1033211208442407/Tomaten-Auberginen-Avocado-Burger.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.154.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 155
    link            = "https://www.chefkoch.de/rezepte/2520581395237137/Wurzelvegetable-Risotto-mit-Gremolata.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.155.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 156
    link            = "https://www.chefkoch.de/rezepte/2352371374010722/Cremiger-Nudelauflauf-mit-Tomaten-und-Mozzarella.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 8
    img             = "IMG.156.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 157
    link            = "https://www.chefkoch.de/rezepte/2725361425059942/Gebackene-sweetkartoffeln-mit-Avocado-Paprika-Creme.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 1
    kitchen          = 8
    img             = "IMG.157.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 158
    link            = "https://www.chefkoch.de/rezepte/2520661395239178/Tomaten-Couscous.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.158.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 159
    link            = "https://www.chefkoch.de/rezepte/1504741255948809/Vegetarische-Tortellini-Pfanne.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.159.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 160
    link            = "https://www.chefkoch.de/rezepte/1754661285144532/Wuerziges-Kartoffelcurry.html"
    duration       = 25
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 8
    img             = "IMG.160.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 161
    link            = "https://www.chefkoch.de/rezepte/3136461467112858/Chefkoch-Rievkooche-Burger.html"
    duration       = 40
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 9
    img             = "IMG.161.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 162
    link            = "https://www.chefkoch.de/rezepte/2801191432230478/Dal-Rote-Linsen.html"
    duration       = 10
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.162.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 163
    link            = "https://www.chefkoch.de/rezepte/2180871350202217/Veganes-basisches-Chili.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.163.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 164
    link            = "https://www.chefkoch.de/rezepte/3207211477346212/Schnelles-Spinat-Kichererbsen-Gericht.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.164.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 165
    link            = "https://www.chefkoch.de/rezepte/2079731336057473/Blumenkohl-aus-dem-Ofen.html"
    duration       = 5
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.165.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 166
    link            = "https://www.chefkoch.de/rezepte/3499511521377959/Pulled-Pilz-mit-Kraeuterseitlingen.html"
    duration       = 5
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.166.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 167
    link            = "https://www.chefkoch.de/rezepte/2455511386627445/Quinoa-Powersalat-mit-Tomaten-und-Avocado.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.167.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 168
    link            = "https://www.chefkoch.de/rezepte/984331203854306/Meine-veganen-Linsenbratlinge.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.168.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 169
    link            = "https://www.chefkoch.de/rezepte/2686111421307206/Raffiniertes-Curry-mit-Mango-Kuerbis-und-Cashewkernen.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.169.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 170
    link            = "https://www.chefkoch.de/rezepte/3740951568031314/Currysuppe-mit-Maultaschen.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.170.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 171
    link            = "https://www.chefkoch.de/rezepte/3048891457520625/Teriyaki-Tofu-mit-Chicoree.html"
    duration       = 15
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.171.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 172
    link            = "https://www.chefkoch.de/rezepte/3952961605784719/Vegan-Wellington-festlicher-veganer-Braten-fuer-Weihnachten.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.172.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 173
    link            = "https://www.chefkoch.de/rezepte/4045331625120015/Pilz-Schawarma-al-Pastor.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.173.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 174
    link            = "https://www.chefkoch.de/rezepte/3274371486501413/Veganes-Soja-Chicken-Korma.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.174.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 175
    link            = "https://www.chefkoch.de/rezepte/1387481243796887/Rote-Linsen-Kokossuppe.html"
    duration       = 10
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.175.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 176
    link            = "https://www.chefkoch.de/rezepte/2356341374556671/Griechische-dicke-weisse-Bohnen-in-Tomatensosse.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.176.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 177
    link            = "https://www.chefkoch.de/rezepte/493511143711461/Koelkasts-Spaghetti-mit-kalter-Tomatensosse.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.177.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 178
    link            = "https://www.chefkoch.de/rezepte/2826761434715126/Linsencurry.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.178.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 179
    link            = "https://www.chefkoch.de/rezepte/2751661427199893/Mamas-vegane-Linsensuppe.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 0
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 9
    img             = "IMG.179.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 180
    link            = "https://www.chefkoch.de/rezepte/3287961488264893/Jackfruit-Burger.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 1
    kitchen          = 9
    img             = "IMG.180.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 181
    link            = "https://www.chefkoch.de/rezepte/2193241351950873/Mediterraner-Nudelsalat-mit-Rucola.html"
    duration       = 25
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.181.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 182
    link            = "https://www.chefkoch.de/rezepte/601861159947648/Italienischer-Brotsalat.html"
    duration       = 20
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.182.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 183
    link            = "https://www.chefkoch.de/rezepte/982331203688547/Italienische-Minestrone.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.183.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 184
    link            = "https://www.chefkoch.de/rezepte/1995841323271256/Albertos-Spaghetti-mit-Meatballs.html"
    duration       = 40
    difficulty   = 1
    milkproducts    = 1 
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 10
    img             = "IMG.184.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 185
    link            = "https://www.chefkoch.de/rezepte/2109501340136606/Tagliatelle-al-Salmone.html"
    duration       = 10
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 1
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.185.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 186
    link            = "https://www.chefkoch.de/rezepte/1518811257110128/Antipasti.html"
    duration       = 40
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.186.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 187
    link            = "https://www.chefkoch.de/rezepte/1186971224658128/Nudelsalat-mit-getrockneten-Tomaten-Pinienkernen-Schafskaese-und-Basilikum.html"
    duration       = 25
    difficulty   = 0
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.187.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 188
    link            = "https://www.chefkoch.de/rezepte/509691146579678/Hackbraten-auf-italienische-Art.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.188.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 189
    link            = "https://www.chefkoch.de/rezepte/772011180069862/Die-echte-Sauce-Bolognese.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 10
    img             = "IMG.189.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 190
    link            = "https://www.chefkoch.de/rezepte/745721177147257/Lasagne.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 10
    img             = "IMG.190.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 191
    link            = "https://www.chefkoch.de/rezepte/2352371374010722/Cremiger-Nudelauflauf-mit-Tomaten-und-Mozzarella.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.191.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 192
    link            = "https://www.chefkoch.de/rezepte/620981162378686/Tortellinisalat-italienische-Art.html"
    duration       = 30
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.192.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 193
    link            = "https://www.chefkoch.de/rezepte/1342861239100533/Tortellini-alla-panna.html"
    duration       = 10
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.193.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 194
    link            = "https://www.chefkoch.de/rezepte/1231981228220302/Spinatlasagne.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.194.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 195
    link            = "https://www.chefkoch.de/rezepte/1299041235031624/Rigatoni-al-forno.html"
    duration       = 20
    difficulty   = 1
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 10
    img             = "IMG.195.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 196
    link            = "https://www.chefkoch.de/rezepte/166951072615119/Bruschetta-italiana.html"
    duration       = 35
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.196.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 197
    link            = "https://www.chefkoch.de/rezepte/125691053847499/Gefuellte-Schweinefilets-mit-Parmaschinken.html"
    duration       = 25
    difficulty   = 2
    milkproducts    = 1
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 1
    sweet           = 0
    kitchen          = 10
    img             = "IMG.197.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 198
    link            = "https://www.chefkoch.de/rezepte/1687631277047830/Risotto-alla-milanese.html"
    duration       = 30
    difficulty   = 2
    milkproducts    = 1
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.198.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 199
    link            = "https://www.chefkoch.de/rezepte/2659071417547506/Spaghetti-aglio-olio-e-peperoncino.html"
    duration       = 10
    difficulty   = 0
    milkproducts    = 0
    meatproducts  = 0
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.199.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()

    dishID       = 200
    link            = "https://www.chefkoch.de/rezepte/889601194503872/Knusprig-duenne-Pizza-mit-Chorizo-und-Mozzarella.html"
    duration       = 30
    difficulty   = 1
    milkproducts    = 0
    meatproducts  = 1
    fishproducts    = 0
    roughage    = 1
    fruits            = 0
    vegetable         = 1
    oil            = 0
    sweet           = 0
    kitchen          = 10
    img             = "IMG.200.jpg"

    new_gericht = Dishes(
    dishID       = dishID,
    link            = link,
    duration       = duration,
    difficulty   = difficulty,
    milkproducts    = milkproducts,
    meatproducts  = meatproducts,
    fishproducts    = fishproducts,
    roughage    = roughage,
    fruits            = fruits,
    vegetable         = vegetable,
    oil            = oil,
    sweet           = sweet,
    kitchen          = kitchen,
    img             = img
    )
    db.session.add(new_gericht)
    db.session.commit()



    return 'gericht'

#gets the preparation of a dish, could have been added to getHTML
def detailview(dish_link):


    link = dish_link

    response = requests.get(link)
    text_to = BeautifulSoup(response.text, features="html.parser")

    #chefkoch uses articles to seperate the website
    article_s = text_to.body.find_all("article")

    preparation = article_s[2]

    article_name = preparation.h2.text

    #preparation is either in article 2 or three, depending
    if "Zubereitung" in article_name :

        preparation = preparation.div.text #im dritten article, befindet sich die zubereitung im ersten div
    else :
        preparation = article_s[3]
        preparation = preparation.div.text #im dritten article, befindet sich die zubereitung im ersten div

    return preparation 

#checks if the dishes provided within a week, do match with the "Ernährungspyramide"
@fresh.route('/calculatedefizit')
def calculatedefizit(user):

    this_userID = user

    #initializing needs and possible suplements

    needs = {
        "sweet"             : 1,
        "oil"              : 2,
        "vegetable"           : 3,
        "fruits"              : 2,
        "roughage"      : 4,
        "fishproducts"      : 1,
        "meatproducts"    : 1,
        "milkproducts"      : 3
    }

    alternativen = {
        "sweet"             : "Schokolade",
        "oil"              : "Avocado",
        "vegetable"           : "Gurke", 
        "fruits"              : "Banane",
        "roughage"      : "Eier",
        "fishproducts"      : "Lachs",
        "meatproducts"    : "Rind",
        "milkproducts"      : "Milch"
    }

    #initializing comparison array

    needs_filled = {
        "sweet"             : 0,
        "oil"              : 0,
        "vegetable"           : 0,
        "fruits"              : 0,
        "roughage"      : 0,
        "fishproducts"      : 0,
        "meatproducts"    : 0,
        "milkproducts"      : 0
    }

    this_user = User.query.filter_by(id = this_userID).first()

    week = []

    week.append(this_user.week1)
    week.append(this_user.week2)
    week.append(this_user.week3)
    week.append(this_user.week4)
    week.append(this_user.week5)

    #counting

    for dish in week :
        this_dish = Dishes.query.filter_by(dishID = dish).first()


        #no loop possible, because no way to access db via variables as key
        needs_filled["sweet"]           = needs_filled["sweet"]             + this_dish.sweet
        needs_filled["oil"]            = needs_filled["oil"]              + this_dish.oil
        needs_filled["vegetable"]         = needs_filled["vegetable"]           + this_dish.vegetable
        needs_filled["fruits"]            = needs_filled["fruits"]              + this_dish.fruits
        needs_filled["roughage"]    = needs_filled["roughage"]      + this_dish.roughage
        needs_filled["fishproducts"]    = needs_filled["fishproducts"]      + this_dish.fishproducts
        needs_filled["meatproducts"]  = needs_filled["meatproducts"]    + this_dish.meatproducts
        needs_filled["milkproducts"]    = needs_filled["milkproducts"]      + this_dish.milkproducts

    #identify deficits
    deficit = []

    for key in needs :
        if (needs[key] - needs_filled[key]) > 0 :
            deficit.append(key)

    suplements = []
    #get suplements
    for entry in deficit :
        suplements.append(alternativen[entry])

    return suplements

#gets name and ingredients of an chefkoch gericht from html documents
def getHTMLdocument(url, case):
      
    response = requests.get(url)
   
    text_to = BeautifulSoup(response.text, features="html.parser")

    article_z = text_to.body.find_all("article") 

    #ingredients stored in first article
    ingr = article_z[1] 

    #if function is called for displaying week ingredients are needed

    if case == 0 :
  
        #setting up variables for string manipulation
        ingr_list = {} 
        number = 0
        pattern = re.compile(r'\s+')    

        #displayed in table
        ingr_t = ingr.find_all("table")   

        #can be multiple tables
        for table in ingr_t :
            ingr_b = table.find_all("tbody") 

            #going through a table
            for tbody in ingr_b :
                ingr_rows = tbody.find_all("tr") 

                
                #going through rows of a single table
                for s_row in ingr_rows : 
                    num_str         = str(number)

                    #manypulating text so its clean displayed later on
                    tds             = s_row.find_all("td")
                    quantity        = tds[0].text.strip()
                    quantity        = re.sub(pattern, '', quantity)
                    name            = tds[1].text.strip()

                    #dict entry
                    ingr_list["menge" + num_str]  = quantity
                    ingr_list["name" + num_str]   = name

                    number = number + 1


        dish_title = article_z[0].div.h1.text  
    
        return ingr_list, dish_title

    #else for mcswipe only the dish name is needed
    else :

        dish_title = article_z[0].div.h1.text 
    
        return dish_title

#simple login
@fresh.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST" :
        email       = request.form.get('email')
        password    = request.form.get('password')

        user = User.query.filter_by(mail=email).first()

        if user:
            if user.password == password:
               
                login_user(user, remember=True)
                return redirect(url_for("fresh.weekplan"))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

        return render_template("login.html")


    return render_template("login.html")

#simple signup
@fresh.route('/sign_up', methods=['GET', 'POST'])
def sign_up():

    if request.method == "POST" :
        email       = request.form.get('email')
        password1   = request.form.get('password1')
        password2   = request.form.get('password2')
        firstname   = request.form.get("firstName")
        name        = request.form.get("lastName")
        veg        = request.form.get("vegan")
        print(veg)

        user = User.query.filter_by(mail=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(firstname) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif len(name) < 2:
            flash('Last name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            #depending on checkbox, user is vegan or not
            if veg == None :
                vegan = 0
            else :
                vegan = 1
            
            new_user = User(
                mail        = email, 
                vorname     = firstname,
                name        = name,
                password    = password1,
                premium     = 0,
                vegan       = vegan
                )
            
            print(vegan)

            db.session.add(new_user)
            db.session.commit()

            #setting up initial swipe to get ratings, so ai can perform

            dishes = setup_first()


            login_user(new_user, remember=True)
            flash('Account created!', category='success')

            #let him swipe
            return render_template("mcswipe.html", dishes=dishes)
  

    return render_template("sign_up.html")

#gets random dishes for a swipe
def setup_first() :

    user_id = current_user.id

    this_user = User.query.filter_by(id = user_id).first()

    vegan = this_user.vegan

    #if the user is vegan he only gets in touch with vegan dishes
    if vegan == 1 :

        list_dishes = Dishes.query.filter_by(meatproducts=0, fishproducts=0, milkproducts=0).order_by(func.random()).limit(10)
    else:
        list_dishes = Dishes.query.order_by(func.random()).limit(10)

    dishes = []
    #get dish data
    for dish in list_dishes:

        single_dish = []

        link_ger = dish.link
        dish_name = getHTMLdocument(link_ger, 1)
        dish_img  = dish.img
        dish_id   = dish.dishID
                
        single_dish.append(dish_name)
        single_dish.append(dish_img)
        single_dish.append(dish_id)


        dishes.append(single_dish)

    return dishes

#called after an mcswipe
@fresh.route('/addratings', methods=['GET', 'POST'])
def addratings():

    #fetches post data
    data = request.get_json()
    print(data)

    data_for_r = data

    len_dic = len(data_for_r)
    accessed = 0

    user_id = current_user.id

    this_date = date.today()

    #for each entry a new db entry gets created
    
    for i in range(10) :
       
        dish_id = list(data_for_r.values())[accessed]
        rating_index = accessed + 1
       
        rating = list(data_for_r.values())[rating_index]

        accessed = accessed + 2
        

        new_rating      = Rating(
            userID      = user_id,
            dishID      = int(dish_id),
            datum       = this_date,
            rating      = int(rating)
            )

        db.session.add(new_rating)
        db.session.commit()
        

         
    return "done"

#preprocesses the date for makeme
def perme(user_id) :

    
    #gets dishes for db and creates df
    all_dishes          = Dishes.query.all()
    dishes              = pd.DataFrame(query_to_dict(all_dishes))
    print(dishes.head())

    #creating dummies for kategorical and ordinal values
    dishes = pd.get_dummies(dishes,prefix=['kitchen'], columns = ['kitchen'], drop_first=True)
    dishes = pd.get_dummies(dishes,prefix=['difficulty'], columns = ['difficulty'], drop_first=True)

    print(dishes.head())

    #ratings to df
    user_ratings    = Rating.query.filter_by(userID=user_id).all()
    ratings         = pd.DataFrame(query_to_dict(user_ratings))
    print(ratings.head())

    this_user    = User.query.filter_by(id=user_id).first()

    vegan = this_user.vegan

    todays_date = date.today()
    todays_month = todays_date - pd.DateOffset(months=1)
    todays_month = str(todays_month)

    #blocks dishes, that the user had last month
    blocked_dishes = ratings.loc[(ratings['datum'] > todays_month)] 
    blocked_dishes = blocked_dishes.dishID
    dishes_choice = dishes.drop(blocked_dishes,0)

    #blocks dishes if vegan
    if (vegan == 1) :
        dishes_choice = dishes_choice.query("meatproducts == 0")
        dishes_choice = dishes_choice.query("fishproducts == 0")
        dishes_choice = dishes_choice.query("milkproducts == 0")


    ratings['datum'] = pd.to_datetime(ratings['datum'])
    ratings["datum"] = ratings["datum"].dt.month
    
    #enables cyclic dates as input
    ratings["date_sin"] = np.sin((ratings.datum-1)*(2.*np.pi/12))
    ratings['date_cos'] = np.cos((ratings.datum-1)*(2.*np.pi/12))

    print(ratings.head())
    print(dishes.head())
    print(dishes_choice.head())


    return ratings, dishes, dishes_choice, this_user

#ai model
def makeme(user_id) :
    #could partly be put in above function

    ratings, dishes, dishes_choice, this_user = perme(user_id)

    #ratings and dishes get merged to become model data
    df_model = dishes.merge(ratings, on="dishID") 

    

    todays_date = date.today()
    todays_month = todays_date.month

    #creating predict data set

    month_sin = np.sin((todays_month-1)*(2.*np.pi/12))
    month_cos = np.cos((todays_month-1)*(2.*np.pi/12))

    dishes_choice = dishes_choice.assign(date_cos = month_cos)
    dishes_choice = dishes_choice.assign(date_sin = month_sin)

    
    #just the id is saved
    dishes_fin = dishes_choice["dishID"]
    dishes_fin = dishes_fin.values.tolist() 


    #slice input

    dishes_choice = dishes_choice.drop(["img","dishID","link"], axis=1)

    #define input and output

    df_input = df_model.drop(["link","dishID","rating","ratingID","userID","datum","img"], axis=1)
    
    df_output = df_model.rating

    #ai model

    model = sklearn.neural_network.MLPClassifier(hidden_layer_sizes=(10, ), activation='relu', solver='adam', 
                                                 alpha=0.0001, batch_size='auto', learning_rate='constant', learning_rate_init=0.001, power_t=0.5, 
                                                 max_iter=1000, shuffle=True, random_state=None, tol=0.0001, verbose=False, warm_start=False, momentum=0.9, 
                                                 nesterovs_momentum=True, early_stopping=False, validation_fraction=0.1, beta_1=0.9, beta_2=0.999, epsilon=1e-08, 
                                                 n_iter_no_change=10)

    #training with rating data
    model.fit(df_input, df_output) 

    #for life demo printing results

    print('\n-- Training data --')
    predictions = model.predict(df_input)
    accuracy = sklearn.metrics.accuracy_score(df_output, predictions)
    print('Accuracy: {0:.2f}'.format(accuracy * 100.0))
    print('Classification Report:')
    print(sklearn.metrics.classification_report(df_output, predictions))
    print('Confusion Matrix:')
    print(sklearn.metrics.confusion_matrix(df_output, predictions))
    print('')

    #Evaluate on test data
    #not done, because not needed (to few datasets)

    print('\n---- Test data ----')
    print("not available")

    #predicting dishes the user might like

    predictions_ch = model.predict(dishes_choice)

    #will save either a like or dislike
    pot_dish = [] 
    pot_not = []  

    #dishes_fin equals predictions and contains dishID
    for x in range(len(predictions_ch)) :      
        
        if predictions_ch[x] == 1 :
            pot_dish.append(dishes_fin[x]) 
        else :
            pot_not.append(dishes_fin[x])

        
    
    #if there are enugh dishes the user might like
    if len(pot_dish) >= 5 : 

        
        #if there is a dish he might not like, he gets one random dish to prevent an bubble effect
        if len(pot_not) > 0 :


            monday = random.choice(pot_not) #pot_not = 0
            tuesday = random.choice(pot_dish)
            pot_dish.remove(tuesday)
            wednesday = random.choice(pot_dish)
            pot_dish.remove(wednesday)
            thursday = random.choice(pot_dish)
            pot_dish.remove(thursday)
            friday = random.choice(pot_dish)
            pot_dish.remove(friday)
            
        #else user just gets random dishes he might like
        else :
            monday = random.choice(pot_dish)
            tuesday = random.choice(pot_dish)
            pot_dish.remove(tuesday)
            wednesday = random.choice(pot_dish)
            pot_dish.remove(wednesday)
            thursday = random.choice(pot_dish)
            pot_dish.remove(thursday)
            friday = random.choice(pot_dish)
            pot_dish.remove(friday)

      
    #if there are not enough dishes he might like             
    else :  

        #randomly giving him dishes 

        for i in range(len(pot_dish)) :
            pot_not.append(pot_dish[i])

        monday = random.choice(pot_not)
        pot_not.remove(monday)
        tuesday = random.choice(pot_not)
        pot_not.remove(tuesday)
        wednesday = random.choice(pot_not)
        pot_not.remove(wednesday)
        thursday = random.choice(pot_not)
        pot_not.remove(thursday)
        friday = random.choice(pot_not)
        pot_not.remove(friday)
        

    #asign new dishes

    this_user.week1 = monday
    this_user.week2 = tuesday
    this_user.week3 = wednesday
    this_user.week4 = thursday
    this_user.week5 = friday


    db.session.commit()


    return monday,tuesday,wednesday,thursday,friday




