__author__ = 'Fabian'

import pymysql.cursors

# Connect to the database
def query_database(query):
    result = False
    connection = pymysql.connect(host='localhost',
                             user='root',
                             password='',
                             db='nw',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            # print(result)
    finally:
        connection.close()

    return result

def get_article_by_id(artikelId):
    # ich brauche id, rubrik, titel, text
    query = """SELECT hex(artikelId), titel, text FROM artikel WHERE hex(artikelId) = '%s';""" % (artikelId)
    tmp = query_database(query)
    return tmp

def get_annotations_for_proband(probandId,mode='12_34'):
    result = []
    # print probandId, type(probandId)
    query = """SELECT hex(artikelId), praeferenz FROM auswahlPart1, probandArtikelListe WHERE probandID = %d AND probandArtikelListe.auswahlId = auswahlPart1.auswahlId;""" % (probandId)
    tmp = query_database(query)
    # print tmp
    if mode == '12_34':
        for dict in tmp:
            if dict['praeferenz'] < 3:
                result.append((dict['hex(artikelId)'], -1))
            else:
                result.append((dict['hex(artikelId)'], 1))
    elif mode == '1_4':
        for dict in tmp:
            if dict['praeferenz'] == 1:
                result.append((dict['hex(artikelId)'], -1))
            elif dict['praeferenz'] == 4:
                result.append((dict['hex(artikelId)'], 1))

    return result

def get_all_probands():
    result = []

    query = """SELECT DISTINCT proband.probandId, probandAlter, abschluss, probandGeschlecht FROM proband, probandArtikelListe, auswahlPart1 WHERE proband.probandId = probandArtikelListe.probandId AND probandArtikelListe.auswahlId = auswahlPart1.auswahlId AND probandAlter BETWEEN 0 AND 90;"""
    tmp = query_database(query)
    for dict in tmp:
        result.append((dict['probandId'],dict['probandGeschlecht'],dict['probandAlter'],dict['abschluss']))

    return result

def get_ressort_for_article(artikelId):
    result = False
    query = """SELECT ressortId FROM artikel WHERE hex(artikelId) = '%s';""" % artikelId
    tmp = query_database(query)
    for dict in tmp:
        ressortId = int(dict['ressortId'])
        if ressortId == 1:
            result = "Bielefeld"
        elif ressortId == 2:
            result = "Politik"
        elif ressortId == 3:
            result = "Sport_Bund"
        elif ressortId == 4:
            result = "Kultur"
        elif ressortId == 5:
            result = "Sport_Bielefeld"
    return result

def get_ressort_ratings_for_proband(probandId):
    result = {}

    #likert-skala von 1-5
    query = """SELECT probandInteresseKultur, probandInteresseLokales, probandInteresseLokalsport, probandInteressePolitik, probandInteresseSport FROM proband WHERE probandId = '%d';""" % probandId
    tmp = query_database(query)
    for dict in tmp:
        ressorts = (dict['probandInteresseKultur'],dict['probandInteresseLokales'],dict['probandInteresseLokalsport'],dict['probandInteressePolitik'],dict['probandInteresseSport'])


        result["Bielefeld"] = ressorts[0]
        result["Politik"] = ressorts[1]
        result["Sport_Bund"] = ressorts[2]
        result["Kultur"] = ressorts[3]
        result["Sport_Bielefeld"] = ressorts[4]

    return result

def get_author_for_article(artikelId):
    result = False
    query = """SELECT autor FROM artikel WHERE hex(artikelId) = '%s';""" % artikelId
    tmp = query_database(query)
    for dict in tmp:
        result = dict['autor']
        if result:
            result = result.lower()
    return result

def get_author_list():
    result = []
    query = """SELECT DISTINCT autor FROM artikel WHERE artikelId IN (SELECT artikelId FROM probandArtikelListe);"""
    tmp = query_database(query)
    for dict in tmp:
        author = dict['autor']
        if author:
            author = author.lower()
            result.append(author)
    return result

def get_page_for_article(artikelId):
    result = False
    query = """SELECT seite FROM artikel WHERE hex(artikelId) = '%s';""" % artikelId
    tmp = query_database(query)
    for dict in tmp:
        result = dict['seite']
    return result

def get_age_edu_sex_for_probandId(probandId):
    result = False
    query = """SELECT probandAlter, abschluss, probandGeschlecht FROM proband WHERE NOT probandalter = 99 AND probandId = %d;""" % (probandId)
    tmp = query_database(query)
    # print tmp
    for dict in tmp:
        result = (dict['probandAlter'],dict['abschluss'].lower(),dict['probandGeschlecht'].lower())
    return result

def get_interests_for_proband(probandId):
    result = False
    sql = """SELECT hobbies FROM proband WHERE hobbies != '' AND hobbies NOT LIKE "%%9%%" AND probandId = "%d";""" % probandId
    tmp = query_database(sql)
    for dict in tmp:
        interest = dict['hobbies']
        result = interest
    return result
