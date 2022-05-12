from re import X
import mysql.connector
import pandas as pd
import sklearn as sk
from sklearn.linear_model import LogisticRegression
import os
from datetime import date
import datetime
import numpy as np
import joblib
import numpy as np
import matplotlib.pyplot as plt
import sklearn.model_selection
import sklearn.metrics
import sklearn.neural_network
import random
from bs4 import BeautifulSoup
import requests
import re
import sqlalchemy



# Creating connection object for db
mydb = mysql.connector.connect(
    host = "localhost",
    database = "mcfresch",
    user = "root",
    password = "2001backhaus"
)

cursor = mydb.cursor()
 
import mysql.connector
from mysql.connector import errorcode


#bereitet die daten aus der datenbank für die ki vor

def preprocessing():
    user_id = 1 #aus session bekommen bitte

    query_g = "Select * from gerichte;"
    gerichte = pd.read_sql(query_g,mydb) #tabelle mit allen gerichten

    #macht aus den label encoded columns - one hot encoded columns
    gerichte = pd.get_dummies(gerichte,prefix=['kueche'], columns = ['kueche'], drop_first=True)
    gerichte = pd.get_dummies(gerichte,prefix=['schwierigkeit'], columns = ['schwierigkeit'], drop_first=True)

    

    query_r = "Select * from userratings;"
    userrating = pd.read_sql(query_r,mydb) #tabelle mit den userratings

    query_u = "Select * from user;"
    user = pd.read_sql(query_u,mydb) #tabelle mit allen nutzer

    #print(gerichte.head())
    #print(userrating.head())
    #print(user.head())

    userrating = userrating.query("user_no == @user_id") #alle ratings des aktuellen nutzers finden


    cur_user = user.loc[user['user_no'] == user_id] #daten des aktuellen users finden
    vegan = cur_user.at[0,"vegan"]  #voreinstellungen des nutzers bezüglich der inhaltstoff restriktionen


    todays_date = date.today()
    todays_month = todays_date - pd.DateOffset(months=1) #kunden sollen zumindets einen monat lang nicht das gleiche essen, daher heute vor einem monat finden

    blocked_gerichte = userrating.loc[(userrating['from_date'] > todays_month)] #gerichte identifizieren, die in dem letzten monat gegessen wurden
    blocked_gerichte = blocked_gerichte.gericht_no #selektion auf id beschränken
    gerichte_ch = gerichte.drop(blocked_gerichte,0) #gerichte filtern, nach geblockten, um tabelle zu erhalten, aus denen der nutzer wählen kann

    #voreinstellungen zur ernährung prüfen um die gerichtauswahl weiter einzurschränken

    if (vegan == 0) :
        gerichte_ch = gerichte_ch.query("fleischprodukt == 1")
    if (vegan == 1) :
        gerichte_ch = gerichte_ch.query("fleischprodukt == 1")
        gerichte_ch = gerichte_ch.query("fischprodukt == 1")
        gerichte_ch = gerichte_ch.query("milchprodukt == 1")

    #skalieren des ratingdatums auf monate 

    userrating['from_date'] = pd.to_datetime(userrating['from_date'])
    userrating["from_date"] = userrating["from_date"].dt.month

    #erzeugen einer zyklischen abbildung für das ki training

    userrating["date_sin"] = np.sin((userrating.from_date-1)*(2.*np.pi/12))
    userrating['date_cos'] = np.cos((userrating.from_date-1)*(2.*np.pi/12))
    

    return cur_user, userrating, gerichte, gerichte_ch

def create_week():

    user_id = 1
    cur_user, userrating, gerichte, gerichte_ch = preprocessing()


    df_model = gerichte.merge(userrating, on="gericht_no") #erzeugen des modeldatensatzes

    #nächster absatz kann eigentlich in die funktion darüber
    #hier wird der datensatz aus dem dem nutzer voschläge gemacht werden angepasst, damit der input gleich bleibt

    todays_date = date.today()
    todays_month = todays_date.month

    #auch zyklische ausrichtung

    month_sin = np.sin((todays_month-1)*(2.*np.pi/12))
    month_cos = np.cos((todays_month-1)*(2.*np.pi/12))

    gerichte_ch = gerichte_ch.assign(date_cos = month_cos)
    gerichte_ch = gerichte_ch.assign(date_sin = month_sin)

    #alle verfügbaren gerichte nur mit index speichern

    gerichte_fin = gerichte_ch["gericht_no"]
    gerichte_fin = gerichte_fin.values.tolist() #umwandlung in liste erfolgt, damit später über die listen länge, welche mit der vorhersage menge übereinstimmt, das sortieren der gerichte erfolgen kann


    #für auswahl daten auf input vorbereiten

    gerichte_ch = gerichte_ch.drop(["picture","gericht_no","link"], axis=1)

    # input und output für modeltraining mit userratings vorbereiten

    df_input = df_model.drop(["link","gericht_no","rating","rating_no","user_no","from_date","picture"], axis=1)
    df_input.to_excel("input.xlsx") 
    df_output = df_model.rating

    #model erstellen (neuronales netz mit bis zu 10 schichten, einfacher classifications output (eine node))

    model = sklearn.neural_network.MLPClassifier(hidden_layer_sizes=(10, ), activation='relu', solver='adam', 
                                                 alpha=0.0001, batch_size='auto', learning_rate='constant', learning_rate_init=0.001, power_t=0.5, 
                                                 max_iter=1000, shuffle=True, random_state=None, tol=0.0001, verbose=False, warm_start=False, momentum=0.9, 
                                                 nesterovs_momentum=True, early_stopping=False, validation_fraction=0.1, beta_1=0.9, beta_2=0.999, epsilon=1e-08, 
                                                 n_iter_no_change=10)

    model.fit(df_input, df_output) #training mit userratings

    #einfaches ausgeben der trainingsergebnisse (werden nicht veröffentlicht)

    print('\n-- Training data --')
    predictions = model.predict(df_input)
    accuracy = sklearn.metrics.accuracy_score(df_output, predictions)
    print('Accuracy: {0:.2f}'.format(accuracy * 100.0))
    print('Classification Report:')
    print(sklearn.metrics.classification_report(df_output, predictions))
    print('Confusion Matrix:')
    print(sklearn.metrics.confusion_matrix(df_output, predictions))
    print('')
    # Evaluate on test data

    print('\n---- Test data ----')

    #vorhersage neuer gerichte

    predictions_ch = model.predict(gerichte_ch)

    pot_ger = [] #speichert alle gerichte ids, die als gut vorhergesagt werden
    pot_nicht = []  #speichert alle gerichte, die als schlecht vorhergesagt werden

    #EINFÜGEN: was wenn pot_nicht == 0
    #HIER MUSS EIN FEHLER SEIN 4.0 ist doppelt

    for x in range(len(predictions_ch)) :      
        
        if predictions_ch[x] == 1 :
            pot_ger.append(gerichte_fin[x]) #ids der gerichte werden gespeichert 
        else :
            pot_nicht.append(gerichte_fin[x])

    
    if len(pot_ger) >= 4 : #wenn genug gerichte für eine woche als schmeckt identifiziert wurden

        #montags wird ein gericht vorgeschlagen, welches nicht schmeckt, um eventuelle neue orientierungen des kunden zu erfahren und potentielles overfitting zu verlangsammen
        #ansonsten erfolgt das zufällige auswählen von gerichten

        monday = random.choice(pot_nicht)
        tuesday = random.choice(pot_ger)
        pot_ger.remove(tuesday)
        wednesday = random.choice(pot_ger)
        pot_ger.remove(wednesday)
        thursday = random.choice(pot_ger)
        pot_ger.remove(thursday)
        friday = random.choice(pot_ger)
        pot_ger.remove(friday)
                   
    else :  #nicht genug gute gerichte

        #es werden die guten und schlechten bunt gemischt und zufällig gewählt
        #EINFÜGEN, es werden so viele gute gewählt wie möglich -> dafür variabeln namen der tage ändern und schleife verwenden

        for i in range(len(pot_ger)) :
            pot_nicht.append(pot_ger[i])

        monday = random.choice(pot_nicht)
        tuesday = random.choice(pot_nicht)
        pot_nicht.remove(tuesday)
        wednesday = random.choice(pot_nicht)
        pot_nicht.remove(wednesday)
        thursday = random.choice(pot_nicht)
        pot_nicht.remove(thursday)
        friday = random.choice(pot_nicht)
        pot_nicht.remove(friday)

    #die aktuelle woche wird in der nutzer tabelle überschrieben

    sql = """UPDATE user SET 
                week1 = %s, 
                week2 = %s,
                week3 = %s,
                week4 = %s,
                week5 = %s
                WHERE user_no = %s"""

    cursor.execute(sql, (monday, tuesday, wednesday, thursday, friday, user_id))

    mydb.commit()

    return monday,tuesday,wednesday,thursday,friday 

###!!!! done


def create_user() : #neuer nutzer wird eingefügt, variablen belegung aus POST

    user_name = "backhaus"
    user_vorname = "moritz"
    user_mail = "youX@mein.gmx"
    user_no = 2
    password = "2001backhaus"
    premium = 1
    vegan = 0


    sql = """Insert INTO user 
            (user_no, vorname, name, mail, password, premium, vegan)
            VALUES
            (%s, %s, %s, %s, %s, %s, %s)    #platzhalter
            """

    cursor.execute(sql, (user_no, user_vorname, user_name, user_mail, password, premium, vegan))    #variablen für sql statement ergänzen (sicherheit überprüfen)

    mydb.commit()

###!!!! done

def getHTMLdocument(url):
      
    #fängt den htlm text ab

    response = requests.get(url)
   
    #codierena als bs4 element, welches tree-like zugriffer erlaubt

    text_to = BeautifulSoup(response.text, features="html.parser")

    article_z = text_to.body.find_all("article") #in dem html elemnt article werden auf chefkoch alle relevanten infos für uns gehalten
    zutaten = article_z[1] #zutaten befinden sich im zweiten element auf dder ganzen seite
  

    zutaten_auf = {} #menge und name der zutat werden in einem dict gespeichert
    number = 0
    pattern = re.compile(r'\s+')    #wird verwendet, um die leerzeichen im webtext zu löschen

    zutaten_t = zutaten.find_all("table")   #zutaten werden in mehreren table elementen gehalten

    for table in zutaten_t :
        zutaten_b = table.find_all("tbody") #speziell im tbody, thead muss ignoeriert werden, da er ebenfalls tr enthält

        for tbody in zutaten_b :
            zutaten_rows = tbody.find_all("tr") #tr ist eine row und erhält menge sowie name

            #speichert die entsprechenden strings in dem dict
            #hohe zugriffszeiten bei vielen iterationen
            
            for reihe in zutaten_rows : 
                num_str = str(number)
                tds = reihe.find_all("td")
                menge = tds[0].text.strip()
                menge = re.sub(pattern, '', menge)
                name = tds[1].text.strip()
                zutaten_auf["menge" + num_str] = menge
                zutaten_auf["name" + num_str] = name
                number = number + 1


    gericht_title = article_z[0].div.h1.text #holt den gericht namen, bs4 gibt, bei einfacher referenzierung immer das erste auftretenden element wieder 
  
    return zutaten_auf, gericht_title

###!!!! done

def create_view() : #erstellt die wochenansicht

    user_id = 1

    query_u = "Select * from user;"
    user = pd.read_sql(query_u,mydb) 

    cur_user = user.loc[user['user_no'] == user_id] #userinfos werden geladen, damit die wochengerichte gefunden werden können
    

    query_g = "Select * from gerichte;"
    gerichte = pd.read_sql(query_g,mydb)

    week = []
    week.append(cur_user.at[0,"week1"])
    week.append(cur_user.at[0,"week2"])
    week.append(cur_user.at[0,"week3"])
    week.append(cur_user.at[0,"week4"])
    week.append(cur_user.at[0,"week5"])


    week_gericht = gerichte.loc[gerichte['gericht_no'].isin(week)] #table, aus dem die informationen der einzelen woche geladen werden
    
    #EINFÜGEN defizit funktion

    defizite = create_defizit(week_gericht)


    #für jedes gericht in der woche werden die zutaten und der titel geholt für das erstellen des einkaufzettels
    zutaten_woche = {}
    gerichte_title = {}

    for i in range(len(week)) :
        link = week_gericht.loc[week[i]]["link"]
        z,g = getHTMLdocument(link)
        zutaten_woche["week" + str(i)] = z
        gerichte_title["week" + str(i)] = g

    print(zutaten_woche)

    #EINFÜGEN einkaufszettel funktion, um stings ordentlich zu formatieren


#####!!!!!!!!!! create_gericht ist done


def create_gericht() : #funktion liefert informationen für die detailierte gericht ansicht (möglicher weise in der andern mit integrieren und output filtern)

    query_g = "Select * from gerichte WHERE gericht_no = 4;" #WICHTIG durch variable ersetzen
    gerichte = pd.read_sql(query_g,mydb)

    link = gerichte.loc[0]["link"]

    response = requests.get(link)
    text_to = BeautifulSoup(response.text, features="html.parser")

    article_z = text_to.body.find_all("article")

    zubereitung = article_z[2]

    zubereitung = zubereitung.div.text #im dritten article, befindet sich die zubereitung im ersten div

    print(zubereitung)

###!!!! done

    
def create_rating() : #neues raitng in der datenbank anlegen, nach dem der user geswipet hat

    user_no = 1
    gericht_no = 1
    from_date = date.today()
    rating = 1

    sql = """Insert INTO userratings 
        (user_no, gericht_no, from_date, rating)
        VALUES
        (%s, %s, %s, %s)
        """

    cursor.execute(sql, (user_no, gericht_no, from_date, rating))

    mydb.commit()

###!!!! done

def create_defizit(week_gerichte) :

    #soll bedarfe nach pyramide

    anzahl_gruppen = {
        "suess" : 1,
        "fett" : 2,
        "gemuese" : 3,
        "obst" : 2,
        "ballaststoffe" : 4,
        "fischprodukte" : 1,
        "fleischprodukt" : 1,
        "milchprodukt" : 3
    }

    #ist bedarfe standard

    anzahl_woche = {
        "suess" : 0,
        "fett" : 0,
        "gemuese" : 0,
        "obst" : 0,
        "ballaststoffe" : 0,
        "fischprodukte" : 0,
        "fleischprodukt" : 0,
        "milchprodukt" : 0
    }

    #ermitteln ist bedarfe

    for index,row in week_gerichte.iterrows() :

        
        for key in anzahl_woche:

            anzahl_woche[key] = anzahl_woche[key] + row[key]

    defizit = [] #speichert defizite

    #abgleich und defizit sammlung

    for key in anzahl_woche :
        if anzahl_woche[key] <anzahl_gruppen[key] :

            defizit.append(key)
         
    return defizit

def main():
   
    #create_rating()
    #create_gericht()
    #create_view()
    #create_user()
    #day_1,day_2,day_3,day_4,day_5 = create_week()
    print("ok")

if __name__ == "__main__": main()
