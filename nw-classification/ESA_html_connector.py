# -*- coding: utf-8 -*-




import requests
import urllib

num_artikelId = 0
num_user = 0

output_file = '/Users/Fabian/Desktop/output_Esa_connector.txt'


def write_to_file(output_file, string):
    f = open(output_file,'w')
    f.write(string)
    f.close()


#Next: variablen in request einfügen. Output normalisieren. vector similarity berechnen. feature basteln. testen

def esa_vec_for_artikelId(artikel,numberArticles):
    #Anfrage für einfache ArtikelId
    artikelId = artikel.id
    title = artikel.title
    # print title

    URL = "http://sc-kognihome.techfak.uni-bielefeld.de/EsaService/webresources/rawInput?artikelid=%s&numberArticles=%d" % (artikelId.lower(),numberArticles)
    URL = URL.strip()

    dict = {}

    try:
        r1 = requests.get(URL,'utf-8')
        # r1 = requests.get("http://sc-kognihome.techfak.uni-bielefeld.de/EsaService/webresources/rawInput?artikelid=61292e0e081f7f1219aa6103e7e43ded70714bfdcea5354c",'utf-8')
        r1.encoding = "utf-8"

        dict = eval(r1.json()['WikipediaAllPersons'])
    except requests.exceptions.ConnectionError as e:
        message = "Verbindung bei Anfrage abgebrochen. URL: %s" % URL
        write_to_file(output_file, message + "\n")
        # write_to_file(output_file, e)
        print message
        print e.message
    except ValueError as e:
        message = "String nicht richtig formatiert. URL: %s" % URL
        write_to_file(output_file, message + "\n")
        # write_to_file(output_file, e)
        print message
        print e.message


    if len(dict.keys()) == 0:

        artikelId = artikel.id[1:]

        URL = "http://sc-kognihome.techfak.uni-bielefeld.de/EsaService/webresources/rawInput?artikelid=%s&numberArticles=%d" % (artikelId.lower(),numberArticles)
        URL = URL.strip()

        dict = {}

        try:
            r1 = requests.get(URL,'utf-8')
            # r1 = requests.get("http://sc-kognihome.techfak.uni-bielefeld.de/EsaService/webresources/rawInput?artikelid=61292e0e081f7f1219aa6103e7e43ded70714bfdcea5354c",'utf-8')
            r1.encoding = "utf-8"

            dict = eval(r1.json()['WikipediaAllPersons'])

        except requests.exceptions.ConnectionError as e:
            message = "Verbindung bei Anfrage abgebrochen. URL: %s" % URL
            write_to_file(output_file, message + "\n")
            # write_to_file(output_file, e)
            print message
            print e.message
        except ValueError as e:
            message = "String nicht richtig formatiert. URL: %s" % URL
            write_to_file(output_file, message + "\n")
            # write_to_file(output_file, e)
            print message
            print e.message

        if len(dict.keys()) == 0:
            print "Keine Ergebnisse fuer %s :  %s" % (artikelId,title)
            print URL

    # print URL

    return dict

def esa_vec_for_interests(interestList,numberArticles):
    #Anfrage nach Interessen

    if interestList:
        interests = interestList[0]

        for i in range(1,len(interestList)):
            interests += ',' + interestList[i]

        # print interests

        URL = "http://sc-kognihome.techfak.uni-bielefeld.de/EsaService/webresources/rawInput?interests=%s&onlyPersons=false&numberArticles=%d" % (interests,numberArticles)
        URL = URL.strip()

        list = []

        try:

            r2 = requests.get(URL,'utf-8')
            r2.encoding = 'utf-8'

            list = r2.json()
        except requests.exceptions.ConnectionError as e:
            message = "Verbindung bei Anfrage abgebrochen. URL: %s" % URL
            write_to_file(output_file, message + "\n")
            # write_to_file(output_file, e)
            print message
            print e.message
        except ValueError as e:
            message = "String nicht richtig formatiert. URL: %s" % URL
            write_to_file(output_file, message + "\n")
            # write_to_file(output_file, e)
            print message
            print e.message


        dict = {}

        for entry in list:
            dict[entry['WikipediaId']] = entry['Score']

        if len(dict.keys()) == 0:
            print "Esa nach Interessen gibt nichts zurück!"
            print URL

        return dict
    else:
        print "Keine Interessen angegeben"
        return {}







