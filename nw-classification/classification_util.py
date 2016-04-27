# -*- coding: utf-8 -*-
__author__ = 'Fabian'

import numpy as np
import nltk
import db_connector
import re
import operator
import stanford_postagger
import ESA_html_connector
import codecs
from sklearn import cross_validation
import file_util
from numpy import *

age_groups = ['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89','90-99']
sexes = ['männlich','weiblich']
edus = ['mittlere reife', 'abitur', 'hochschulabschluss', 'sonstiges']
ressorts = ['Bielefeld', 'Sport_Bielefeld', 'Kultur', 'Politik', 'Sport_Bund']
page_categories = ['1','2','3','4-5','6-7','8','9-16','17-24','25+']
word_count_categories = [0,1,2,3,4,5]
stopword_tags = ['APPR','APPRART','APPO','APZR','ART','ITJ','KOUI','KOUS','KON','KOKOM']
fold_mode = 'article'

number_top_topics = []

number_articles_esa = 100



article_dict = {}
user_dict = {}
proband2articles = {}






class Artikel:
    def __init__(self, id):
        articleInfo = db_connector.get_article_by_id(id)
        self.id = id
        self.title = articleInfo[0]['titel']
        #hier direkt encoding ueberarbeiten?
        self.fulltext = articleInfo[0]['text']
        self.unigrams = [tok for tokens in self.tokenize(self.fulltext, 1) for tok in tokens]
        self.bigrams = ["%s_%s"%(i,j) for (i,j) in self.tokenize(self.fulltext, 2)]
        self.titleTokens = [tok for tokens in self.tokenize(self.title, 1) for tok in tokens]
        self.ressort = db_connector.get_ressort_for_article(id)
        self.normalized_ressort = self.normalize_ressort_to_dict()
        self.author = clean_author_list([db_connector.get_author_for_article(self.id)])
        self.wordCountText = len(self.unigrams)
        self.wordCountTitle = len(self.titleTokens)
        self.normalized_word_count_text = self.normalize_word_count()
        self.page = int(db_connector.get_page_for_article(id))
        self.page_normalized = self.normalize_pages()
        self.bow = self.create_bag_of_words()
        self.bow_filtered = self.create_bag_of_words(filter_stopwords=True)
        self.bow_bigrams = self.create_bigram_bag_of_words()
        self.esa_vec = self.create_esa_dict(number_articles_esa)
        self.esa_vec_normalized = normalize_esa_vector(self.esa_vec)
        self.top_esa_topics = self.find_top_esa_topics()

    def create_esa_dict(self, number_articles_esa):
        dict = ESA_html_connector.esa_vec_for_artikelId(self, number_articles_esa)
        for key in dict.keys():
            dict[key] = float(dict[key])
        return dict


    def find_top_esa_topics(self):
        avg_esa_value = np.mean([float(value) for value in self.esa_vec.values()])
        top_esa_topics_dict = {}
        for key in self.esa_vec.keys():
            if float(self.esa_vec[key]) >= avg_esa_value:
                top_esa_topics_dict[key] = float(self.esa_vec[key])
        number_top_topics.append(len(top_esa_topics_dict.keys()))
        return top_esa_topics_dict

    def compareTitleToInterests(self, interestList, mode = 'prior'):
        feature = {}

        feature['title_' + mode] = 0

        # for interest in interestList:
        #     if type(interest) == tuple:
        #         interest = interest[0]
        #     feature[interest + '_title_' + mode] = 0
        #     for word in re.split("\W", self.title):
        #         if (interest.lower().decode('utf-8')) == (word.lower().decode('utf-8')):
        #             feature[interest + '_title_' + mode] = 1

        for interest in interestList:
            if type(interest) == tuple:
                interest = interest[0]
            for word in re.split("\W", self.title):
                if (interest.lower().decode('utf-8')) == (word.lower().decode('utf-8')):
                    feature['title_' + mode] = 1

        return feature

    def compareTextToInterests(self, interestList, mode = 'prior'):
        feature = {}

        # for interest in interestList:
        #     if type(interest) == tuple:
        #         interest = interest[0]
        #     feature[interest + '_text_' + mode] = 0
        #     for word in re.split("\W", self.fulltext):
        #         if (interest.lower().decode('utf-8')) == (word.lower().decode('utf-8')):
        #             feature[interest + '_text_' + mode] = 1

        feature['text_' + mode] = 0

        for interest in interestList:
            if type(interest) == tuple:
                interest = interest[0]

            for word in re.split("\W", self.fulltext):
                if (interest.lower().decode('utf-8')) == (word.lower().decode('utf-8')):
                    feature['text_' + mode] = 1

        return feature

    def compareRessortToRessortRatings(self, ressort_ratings, threshold = 3):
        result = {}

        proband_ressort_dict = ressort_ratings

        for key in proband_ressort_dict:
            dict_entry = "ressort_specific_%s" % key
            if key == self.ressort and proband_ressort_dict[key] >= threshold:
                result[dict_entry] = 1
            else:
                result[dict_entry] = 0

        return result

    def getTitle(self):
        return self.title

    def getFullText(self):
        return self.fulltext

    def tokenize(self, s, n=1): #use n to return unigrams (n=1) or bigrams (n=2)
        tokens = [tok.lower() for tok in nltk.word_tokenize(s) if not tok in ".,:;()!?"]
        spans = [(i, i) for i in range(len(tokens))]
        if n > 1:
            return [tokens[i:(j+n)] for i,j in spans[:-n]]
        else:
            return [tokens[i:(j+n)] for i,j in spans]

    def normalize_ressort_to_dict(self):
        tmp = {'Sport_Bielefeld': 0, 'Kultur': 0, 'Bielefeld': 0, 'Politik': 0, 'Sport_Bund': 0}
        result = {}
        for key in tmp:
            dict_entry = "ressort_prior_%s" % key
            if key == self.ressort:
                result[dict_entry] = 1
            else:
                result[dict_entry] = 0
        return result

    def normalize_word_count(self):
        if self.wordCountText < 100:
            return 0
        elif self.wordCountText < 200:
            return 1
        elif self.wordCountText < 300:
            return 2
        elif self.wordCountText < 400:
            return 3
        elif self.wordCountText < 500:
            return 4
        else:
            return 5

    def normalize_pages(self):
        dict = {'1':0,'2':0,'3':0,'4-5':0,'6-7':0,'8':0,'9-16':0,'17-24':0,'25+':0}
        if self.page == 1:
            dict['1'] = 1
        elif self.page == 2:
            dict['2'] = 1
        elif self.page == 3:
            dict['3'] = 1
        elif self.page < 6:
            dict['4-5'] = 1
        elif self.page < 8:
            dict['6-7'] = 1
        elif self.page == 8:
            dict['8'] = 1
        elif self.page < 17:
            dict['9-16'] = 1
        elif self.page < 25:
            dict['17-24'] = 1
        else:
            dict['25+'] = 1
        return dict

    def getUnigrams(self):
        return self.unigrams

    def getBigrams(self):
        return self.bigrams

    def getTitleTokens(self):
        return self.titleTokens

    def create_bag_of_words(self, filter_stopwords = True, mode=''):
        bow_dict = {}
        list = self.getUnigrams()
        if filter_stopwords:
            list = []
            tagged_list = tag_word_list(list)
            #TODO: add loop to filter stopwords
            for word,tag in tagged_list:
                if not (tag in stopword_tags):
                    list.append(word)
        for word in list:
            if mode=='binary':
                bow_dict[word] = 1
            else:
                bow_dict[word] = bow_dict.setdefault(word, 0)+1
        return bow_dict

    def create_bigram_bag_of_words(self):
        bow_dict = {}
        for word in self.getBigrams():
            bow_dict[word] = bow_dict.setdefault(word, 0)+1
        return bow_dict

class User:
    def __init__(self, id):
        self.id = id
        self.age, self.edu, self.sex = db_connector.get_age_edu_sex_for_probandId(id)
        self.normalized_age = self.normalize_age()
        self.interests = self.create_interest_list()
        self.ressort_ratings = db_connector.get_ressort_ratings_for_proband(id)
        global proband2articles

        self.annotations = proband2articles[self.id]
        self.esa_vec = ESA_html_connector.esa_vec_for_interests(self.interests, number_articles_esa)
        self.top_esa_topics = self.find_top_esa_topics()
        self.esa_vec_normalized = normalize_esa_vector(self.esa_vec)

    def find_top_esa_topics(self):
        avg_esa_value = np.mean([float(value) for value in self.esa_vec.values()])
        top_esa_topics_dict = {}
        for key in self.esa_vec.keys():
            if float(self.esa_vec[key]) >= avg_esa_value:
                top_esa_topics_dict[key] = float(self.esa_vec[key])
        number_top_topics.append(len(top_esa_topics_dict.keys()))
        return top_esa_topics_dict

    def normalize_age(self):
        decade = int(self.age/10) * 10
        normalized_age = "%d-%d" % (decade, decade + 9)
        return normalized_age

    def create_user_annotation_list(self):
        return db_connector.get_annotations_for_proband(self.id)

    def compute_cross_features(self, artikel):
        cross_features = {}

        #ressort mit features
        cross_features_age_ressort = {}
        cross_features_sex_ressort = {}
        cross_features_edu_ressort = {}

        #seiteregionen mit features
        cross_features_age_page = {}
        cross_features_sex_page = {}
        cross_features_edu_page = {}

        #normalisierte worterzahl mit features
        cross_age_word_count_text = {}
        cross_sex_word_count_text = {}
        cross_edu_word_count_text = {}

        for ressort in ressorts:

            if artikel.ressort == ressort:

                for age in age_groups:
                    feature = "%s_%s" % (ressort,age)
                    if self.normalized_age == age:
                        cross_features_age_ressort[feature] = 1
                    else:
                        cross_features_age_ressort[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (ressort,sex)
                    sex = sex.decode('utf-8')
                    if self.sex == sex:
                        cross_features_sex_ressort[feature] = 1
                    else:
                        cross_features_sex_ressort[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (ressort,edu)
                    if self.edu == edu:
                        cross_features_edu_ressort[feature] = 1
                    else:
                        cross_features_edu_ressort[feature] = 0

            else:

                for age in age_groups:
                    feature = "%s_%s" % (ressort,age)
                    cross_features_age_ressort[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (ressort,sex)
                    cross_features_sex_ressort[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (ressort,edu)
                    cross_features_edu_ressort[feature] = 0

        for page in page_categories:

            if artikel.page_normalized[page] == 1:

                for age in age_groups:
                    feature = "%s_%s" % (page,age)
                    if self.normalized_age == age:
                        cross_features_age_page[feature] = 1
                    else:
                        cross_features_age_page[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (page,sex)
                    sex = sex.decode('utf-8')
                    if self.sex == sex:
                        cross_features_sex_page[feature] = 1
                    else:
                        cross_features_sex_page[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (page,edu)
                    if self.edu == edu:
                        cross_features_edu_page[feature] = 1
                    else:
                        cross_features_edu_page[feature] = 0

            else:

                for age in age_groups:
                    feature = "%s_%s" % (page,age)
                    cross_features_age_page[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (page,sex)
                    cross_features_sex_page[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (page,edu)
                    cross_features_edu_page[feature] = 0

        for word_count_category in word_count_categories:

            if artikel.normalized_word_count_text == word_count_category:

                for age in age_groups:
                    feature = "%s_%s" % (word_count_category,age)
                    if self.normalized_age == age:
                        cross_age_word_count_text[feature] = 1
                    else:
                        cross_age_word_count_text[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (word_count_category,sex)
                    sex = sex.decode('utf-8')
                    if self.sex == sex:
                        cross_sex_word_count_text[feature] = 1
                    else:
                        cross_sex_word_count_text[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (word_count_category,edu)
                    if self.edu == edu:
                        cross_edu_word_count_text[feature] = 1
                    else:
                        cross_edu_word_count_text[feature] = 0

            else:

                for age in age_groups:
                    feature = "%s_%s" % (word_count_category,age)
                    cross_age_word_count_text[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (word_count_category,sex)
                    cross_sex_word_count_text[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (word_count_category,edu)
                    cross_edu_word_count_text[feature] = 0

        cross_features.update(cross_features_age_ressort)
        cross_features.update(cross_features_edu_ressort)
        cross_features.update(cross_features_sex_ressort)
        cross_features.update(cross_features_sex_page)
        cross_features.update(cross_features_age_page)
        cross_features.update(cross_features_edu_page)
        cross_features.update(cross_age_word_count_text)
        cross_features.update(cross_sex_word_count_text)
        cross_features.update(cross_edu_word_count_text)

        return cross_features,cross_features_age_ressort,cross_features_sex_ressort,cross_features_edu_ressort,\
               cross_features_age_page,cross_features_sex_page,cross_features_edu_page,cross_age_word_count_text,\
               cross_sex_word_count_text,cross_edu_word_count_text

    def get_id(self):
        return self.id

    def get_age(self):
        return self.age

    def get_sex(self):
        return self.sex

    def get_edu(self):
        return self.edu

    def get_interests(self):
        return self.interests

    def get_ressort_ratings(self):
        return self.ressort_ratings

    def get_all_info(self):
        return self.id, self.age, self.sex, self.edu, self.interests, self.ressort_ratings

    def create_interest_list(self):
        interests = db_connector.get_interests_for_proband(self.id)

        interestList = []

        # print interests
        if interests:
            interestList = re.compile('\\s*,\\s*|\\s*;\\s*').split(interests)

        result = []

        for interest in interestList:
            result.append((normalize_string(interest).replace(" ","_")))
        # print result
        return result

    def user_specific_esa_topic_comparison(self,article,article_train_test,num_topics = 1):
        global article_dict
        # article_id = article
        # article = article_dict[article]

        result = 0
        counter = 0
        for user_article_id in self.annotations:
            user_article = article_dict[user_article_id[0]]
            if article_train_test[user_article_id[0]] == 1:
                if compare_esa_topics(user_article.top_esa_topics,article.top_esa_topics):
                    counter+=1

        if counter >= num_topics:
            return 1
        else:
            return 0

    def mean_cosine_sim(self, article, article_train_test, distances, index_dict, mode, only_positive_articles=True):
        cos_sims = []
        global article_dict
        article_id = article
        article = article_dict[article]

        for user_article in self.annotations:

            if mode == 4:
                esa_distances = distances
                if article_train_test[user_article[0]] == 1:
                    #nur positiv bewertete artikel nutzen
                    if only_positive_articles:
                        if user_article[1] == 1:
                            user_article_id = user_article[0]
                            cos_sim = esa_distances[index_dict[article_id],index_dict[user_article_id]]
                            cos_sims.append(cos_sim)

                    #nur negativ bewertete artikel nutzen
                    elif not only_positive_articles:
                        if user_article[1] == -1:
                            user_article_id = user_article[0]
                            cos_sim = esa_distances[index_dict[article_id],index_dict[user_article_id]]
                            cos_sims.append(cos_sim)

            if mode == 3:
                unigram_distances = distances
                if article_train_test[user_article[0]] == 1:
                    #nur positiv bewertete artikel nutzen
                    if only_positive_articles:
                        if user_article[1] == 1:
                            user_article_id = user_article[0]
                            cos_sim = unigram_distances[index_dict[article_id],index_dict[user_article_id]]
                            cos_sims.append(cos_sim)

                    #nur negativ bewertete artikel nutzen
                    elif not only_positive_articles:
                        if user_article[1] == -1:
                            user_article_id = user_article[0]
                            cos_sim = unigram_distances[index_dict[article_id],index_dict[user_article_id]]
                            cos_sims.append(cos_sim)

            else:
                if article_train_test[user_article[0]] == 1:

                    #nur positiv bewertete artikel nutzen
                    if only_positive_articles:
                        if user_article[1] == 1:
                            user_article = article_dict[user_article[0]]
                            cos_sim = cosine_sim_articles(article,user_article,mode)
                            cos_sims.append(cos_sim)

                    #nur negativ bewertete artikel nutzen
                    elif not only_positive_articles:
                        if user_article[1] == -1:
                            user_article = article_dict[user_article[0]]
                            cos_sim = cosine_sim_articles(article,user_article,mode)
                            cos_sims.append(cos_sim)

        #falls user keinen artikel positiv bzw negativ bewertet hat ist cos_sims leeres array
        if cos_sims:
            return np.mean(cos_sims),np.min(cos_sims),np.max(cos_sims)
        else:
            return 0.0,0.0,0.0

class NwAnnotations:
    def __init__(self, annotation_mode):
        print "Initialisiere Annotationen..."
        #hier dict mit id:artikel_objekt
        global article_dict
        global proband2articles
        global user_dict
        #hier dict mit proband: artikelliste
        #dict mit 'probandId':[(artikelId, label),(...),...]
        proband2articles = self.create_proband2articles(annotation_mode)
        #dict mit artikelid:artikel_objekt
        article_dict = self.create_article_dict()
        #dict mit probandid:user_objekt
        user_dict = self.create_user_dict()
        #Liste mit allen probandIds : [1,4,6,7,...]
        self.annotators = db_connector.get_all_probands()
        #top interessen (mehr als 1 mal genannt) als Liste von Tupeln
        self.topInterests = self.extract_top_interests(1)

        # self.annotationList = self._create_annotation_lists()
        self.annotationList = proband2articles
        self.authorList = self.create_author_list()
        # self.authorList = []

        self.annotators, self.annotationList = self.filter_annotations(20)
        print "Durschnittliche Anzahl an Top Topics pro Esa-Vektor: %f. Min = %f. Max = %f" % (np.mean(number_top_topics),np.min(number_top_topics),np.max(number_top_topics))
        print "Initialisierung abgeschlossen"

    def create_feature_matrix(self, dynamic=True):

        f2matrix = {}

        title_interest_vector = []
        text_interest_vector = []
        ressort_prior_vector = []
        author_vector = []
        page_normalized_vector = []
        word_count_text_vector = []
        word_count_titel_vector = []
        user_titel_interests_vector = []
        user_text_interests_vector = []
        esa_comparison_1000_0001_vector = []
        cf_vector = []
        cf_age_ressort_vector = []
        cf_sex_ressort_vector = []
        cf_edu_ressort_vector = []
        cf_age_page_vector = []
        cf_sex_page_vector = []
        cf_edu_page_vector = []
        cf_age_word_count_text_vector = []
        cf_sex_word_count_text_vector = []
        cf_edu_word_count_text_vector = []
        yes_no_vector = []
        ressort_specific_vector = []
        ressort_specific_rating_vector = []
        interest_esa_topic_comparison = []


        f2matrix['title_interests'] = 0
        f2matrix['text_interests'] = 1
        f2matrix['ressort_prior'] = 2
        f2matrix['author'] = 3
        f2matrix['page_normalized'] = 4
        f2matrix['word_count_text_normalized'] = 5
        f2matrix['word_count_titel'] = 6
        f2matrix['user_titel_interests'] = 7
        f2matrix['user_text_interests'] = 8
        f2matrix['comparison_1000_0001'] = 9
        f2matrix['cf'] = 10
        f2matrix['cf_age_ressort'] = 11
        f2matrix['cf_sex_ressort'] = 12
        f2matrix['cf_edu_ressort'] = 13
        f2matrix['cf_age_page'] = 14
        f2matrix['cf_sex_page'] = 15
        f2matrix['cf_edu_page'] = 16
        f2matrix['cf_age_word_count_text'] = 17
        f2matrix['cf_sex_word_count_text'] = 18
        f2matrix['cf_edu_word_count_text'] = 19
        f2matrix['yes_no'] = 20
        f2matrix['ressort_specific'] = 21
        f2matrix['ressort_specific_rating'] = 22
        f2matrix['interest_topic_comparison'] = 23




        featureMatrix = [title_interest_vector, #0
                         text_interest_vector,  #1
                         ressort_prior_vector,    #2
                         author_vector,     #3
                         page_normalized_vector,#4
                         word_count_text_vector,#5
                         word_count_titel_vector,#6
                         user_titel_interests_vector,#7
                         user_text_interests_vector,#8
                         esa_comparison_1000_0001_vector,#9
                         cf_vector,#10
                         cf_age_ressort_vector,#11
                         cf_sex_ressort_vector,#12
                         cf_edu_ressort_vector,#13
                         cf_age_page_vector,#14
                         cf_sex_page_vector,#15
                         cf_edu_page_vector,#16
                         cf_age_word_count_text_vector,#17
                         cf_sex_word_count_text_vector,#18
                         cf_edu_word_count_text_vector,#19
                         yes_no_vector,#20
                         ressort_specific_vector,#21
                         ressort_specific_rating_vector,#22
                         interest_esa_topic_comparison#23
                         ]

        if len(f2matrix.keys()) != len(featureMatrix):
            print "Error: Zeiger auf Matrix nicht richtig eingestellt"


        labelVector = []
        proband2fvs = {}    #proband:[fvs]
        fv2artikelId = {}   #fv_index : artikelId
        fv2userId = {}      #fv_index : userId
        probandList = []    #alle untersuchten probanden

        i = 0
        for proband in self.annotators:

            probandId = proband[0]
            probandList.append(probandId)
            fvList = []

            user = user_dict[probandId]

            print "Feature-Vektoren für proband %d werden erstellt..." % probandId
            for annotation in self.annotationList[probandId]:
                artikelId = annotation[0]
                label = annotation[1]
                yes_no_vector.append({'yes_no':label})
                artikel = article_dict[artikelId]

                #Priors
                title_interest_dict = artikel.compareTitleToInterests(self.topInterests, 'prior')
                title_interest_vector.append(title_interest_dict)

                text_interest_dict = artikel.compareTextToInterests(self.topInterests, 'prior')
                text_interest_vector.append(text_interest_dict)

                ressort_prior_vector.append(artikel.normalized_ressort)
                ressort_specific_vector.append(artikel.compareRessortToRessortRatings(user.ressort_ratings))

                #für alle ressorts: binäre features mit 'ressort des artikels interessiert den user zu 5,4,3,2,1.
                #bsp: artikel mit ressort politik. feature: politik interessiert user zu 5 : nein (0)
                ressort_user_specific_binary_ratings = {} #möge mich für diesen Variablennamen der Blitz des Zeus treffen
                for ressort in ressorts:
                    feature_name = 'user_specific_ressort_rating_' + ressort + '_'
                    for j in range (1,6):
                        feature_name+= "%d" % j
                        if user.get_ressort_ratings()[ressort] == j:
                            if artikel.ressort == ressort:
                                ressort_user_specific_binary_ratings[feature_name] = 1
                        else:
                            ressort_user_specific_binary_ratings[feature_name] = 0
                ressort_specific_rating_vector.append(ressort_user_specific_binary_ratings)

                featureDict = {}
                for author in self.authorList:
                    if artikel.author and artikel.author[0] == author:
                        featureDict[author] = 1
                    else:
                        featureDict[author] = 0
                if len(featureDict.keys()) == 0:
                    featureDict['empty'] = 1
                author_vector.append(featureDict)

                page_normalized_vector.append(artikel.page_normalized)

                dict = {}
                dict['word_count_normalized'] = artikel.normalized_word_count_text
                word_count_text_vector.append(dict)

                dict = {'wordCountTitle':artikel.wordCountTitle}
                word_count_titel_vector.append(dict)

                #user-specific
                user_text_interests_vector.append(artikel.compareTextToInterests(user.get_interests(),'specific'))
                user_titel_interests_vector.append(artikel.compareTitleToInterests(user.get_interests(),'specific'))
                cfs = user.compute_cross_features(artikel)
                cf_vector.append(cfs[0])
                cf_age_ressort_vector.append(cfs[1])
                cf_sex_ressort_vector.append(cfs[2])
                cf_edu_ressort_vector.append(cfs[3])
                cf_age_page_vector.append(cfs[4])
                cf_sex_page_vector.append(cfs[5])
                cf_edu_page_vector.append(cfs[6])
                cf_age_word_count_text_vector.append(cfs[7])
                cf_sex_word_count_text_vector.append(cfs[8])
                cf_edu_word_count_text_vector.append(cfs[9])

                numberArticles = 1000
                interest_article_similarity = ESA_compare(artikel.id,user.id,numberArticles)
                esa_comparison_1000_0001_vector.append({'esa_bin_comparison':interest_article_similarity})

                interest_esa_topic_comparison.append({'interest_esa_topic_comparison':compare_esa_topics(artikel.top_esa_topics,user.top_esa_topics)})

                labelVector.append(int(label))

                fv2artikelId[i] = artikelId
                fv2userId[i] = user.id
                fvList.append(i)
                i += 1

            proband2fvs[probandId] = fvList

        lol_labels = leave_one_out_labels(proband2fvs, probandList, fold_mode)

        #jetzt wird hier in jedem train,test-split von lol einmal angezeigt, welche indizes aus lol_labels
        # in train und welche in test sind

        lol = cross_validation.LeaveOneLabelOut(lol_labels)

        dynamic_folds = []


        #hier flag rein?
        if dynamic:

            num_foldings = len(lol)

            print "dynamische features werden erstellt..."
            print "berechne Train und testfolds (%d insgesamt)..." % num_foldings
            for train, test in lol:
                #dict mit den artikel -> in train (1) oder in test (0)
                article_train_test = {}
                for i in train:
                    #fehler: keyerror: 3???
                    # print i,"->",fv2artikelId[i]

                    article_train_test[fv2artikelId[i]] = 1 #in der Trainingsmenge
                for i in test:
                    article_train_test[fv2artikelId[i]] = 0 #in der Testmenge
                dynamic_folds.append(article_train_test)

            #tabelle mit esa-distanzen von artikeln zueinander
            unigram_distances, esa_distances, index_dict = self.precompute_esa_distances()

            #feature-vektoren für jedes folding
            for i in range(0,num_foldings):
                print "berechne dynamische features für fold %d..." % i
                article_train_test = dynamic_folds[i]

                dynamic_unigram_mean_positives_vector = []
                dynamic_unigram_min_positives_vector = []
                dynamic_unigram_max_positives_vector = []
                dynamic_unigram_mean_negatives_vector = []
                dynamic_unigram_min_negatives_vector = []
                dynamic_unigram_max_negatives_vector = []

                dynamic_esa_mean_positives_vector = []
                dynamic_esa_min_positives_vector = []
                dynamic_esa_max_positives_vector = []
                dynamic_esa_mean_negatives_vector = []
                dynamic_esa_min_negatives_vector = []
                dynamic_esa_max_negatives_vector = []

                dynamic_esa_esa_vector = []

                dynamic_vec = [dynamic_esa_mean_positives_vector,dynamic_esa_min_positives_vector,dynamic_esa_max_positives_vector,dynamic_esa_mean_negatives_vector,dynamic_esa_min_negatives_vector,dynamic_esa_max_negatives_vector,
                               dynamic_unigram_mean_positives_vector,dynamic_unigram_min_positives_vector,dynamic_unigram_max_positives_vector,dynamic_unigram_mean_negatives_vector,dynamic_unigram_min_negatives_vector,dynamic_unigram_max_negatives_vector,
                               dynamic_esa_esa_vector
                               ]
                #diese schleife evtl doch mit in die andere packen?
                for probandId in probandList:
                    print "\tproband %d" % probandId
                    for annotation in self.annotationList[probandId]:

                        artikelId = annotation[0]

                        artikel = article_dict[artikelId]

                        #table look-up der esa-distanzen folgt in user.mean_cosine_sim. Dabei werden nur die artikel ausgewählt, die
                        # in der aktuellen article_train_test-aufstellung als 1 markiert sind (die sind in der trainingsmenge)
                        cosine_esa_mean_pos, cosine_esa_min_pos, cosine_esa_max_pos = user.mean_cosine_sim(artikel.id,article_train_test,esa_distances,index_dict,mode = 4, only_positive_articles=True)
                        cosine_esa_mean_neg, cosine_esa_min_neg, cosine_esa_max_neg = user.mean_cosine_sim(artikel.id,article_train_test,esa_distances,index_dict,mode = 4, only_positive_articles=False)

                        #mit den indizes 0-5 auf den esa_vec kann man die einzelnen esa-features ansprechen
                        dynamic_esa_mean_positives_vector.append({'user_cosine_esa_mean_positives': cosine_esa_mean_pos})
                        dynamic_esa_min_positives_vector.append({'user_cosine_esa_min_positives': cosine_esa_min_pos})
                        dynamic_esa_max_positives_vector.append({'user_cosine_esa_max_positives': cosine_esa_max_pos})

                        dynamic_esa_mean_negatives_vector.append({'user_cosine_esa_mean_negatives': cosine_esa_mean_neg})
                        dynamic_esa_min_negatives_vector.append({'user_cosine_esa_min_negatives': cosine_esa_min_neg})
                        dynamic_esa_max_negatives_vector.append({'user_cosine_esa_max_negatives': cosine_esa_max_neg})


                        cosine_unigram_mean_pos, cosine_unigram_min_pos, cosine_unigram_max_pos = user.mean_cosine_sim(artikel.id,article_train_test,unigram_distances,index_dict,mode = 3, only_positive_articles=True)
                        cosine_unigram_mean_neg, cosine_unigram_min_neg, cosine_unigram_max_neg = user.mean_cosine_sim(artikel.id,article_train_test,unigram_distances,index_dict,mode = 3, only_positive_articles=False)

                        #mit den indizes 0-5 auf den esa_vec kann man die einzelnen esa-features ansprechen
                        dynamic_unigram_mean_positives_vector.append({'user_cosine_unigram_mean_positives': cosine_unigram_mean_pos})
                        dynamic_unigram_min_positives_vector.append({'user_cosine_unigram_min_positives': cosine_unigram_min_pos})
                        dynamic_unigram_max_positives_vector.append({'user_cosine_unigram_max_positives': cosine_unigram_max_pos})

                        dynamic_unigram_mean_negatives_vector.append({'user_cosine_unigram_mean_negatives': cosine_unigram_mean_neg})
                        dynamic_unigram_min_negatives_vector.append({'user_cosine_unigram_min_negatives': cosine_unigram_min_neg})
                        dynamic_unigram_max_negatives_vector.append({'user_cosine_unigram_max_negatives': cosine_unigram_max_neg})

                        esa_esa_dict = {}
                        for l in range(1,int(np.mean(number_top_topics))):
                            esa_esa_dict["esa_esa_comparison_%d_topics" % l] = user.user_specific_esa_topic_comparison(artikel, article_train_test, num_topics=l)
                        dynamic_esa_esa_vector.append(esa_esa_dict)

                dynamic_folds[i] = dynamic_vec


        return featureMatrix, dynamic_folds, f2matrix, labelVector, proband2fvs, fv2artikelId, fv2userId, probandList, lol

    def _create_annotation_lists(self):
        #fuer jeden probanden die Annotationen herausfinden
        allAnnotations = {}
        for proband in self.annotators:
            probandId = proband[0]
            annotations = db_connector.get_annotations_for_proband(probandId)
            if len(annotations) > 0:
                allAnnotations[probandId] = annotations
        return allAnnotations

    def create_author_list(self):
        print "Erstelle Autoren Liste"

        result = []
        for key in article_dict.keys():
            article = article_dict[key]
            result.extend(article.author)

        # tmp_authors = clean_author_list(db_connector.get_author_list())
        # # tmp_authors = db_connector.get_author_list()
        # for author in tmp_authors:
        #     if author not in result:
        #         result.append(author)
        print "Liste aller Autoren erstellt"
        return result

    def filter_annotations(self, minimum_annotations):
        annotators = []
        annotation_list = {}

        for i in self.annotators:
            if len(self.annotationList[i[0]]) >= minimum_annotations:
                annotators.append(i)
                annotation_list[i[0]] = self.annotationList[i[0]]

        return annotators, annotation_list

    def extract_top_interests(self, threshold):
        sql = """SELECT hobbies FROM proband WHERE hobbies != '' AND hobbies NOT LIKE "%%9%%";"""
        interestSet = db_connector.query_database(sql)
        sortedInterests = count_interests(interestSet)
        result = []
        for i in range(0,len(sortedInterests)):
            if sortedInterests[i][1] > threshold:
                result.append(sortedInterests[i])
        return result

    def checkClassSize(self, labelVector):
        class_size = 10
        i = 0
        j = 0
        for label in labelVector:
            if label == 1:
                i += 1
            elif label == -1:
                j += 1
        if i < class_size or j < class_size:
            return False
        else:
            return True

    def precompute_esa_distances(self):
        print "berechne esa-distanzen..."
        number_articles = len(article_dict.keys())

        dist_zero_esa = 0
        dist_zero_unigram = 0
        num_dist_computations = 0

        #in den zeilen i = 0,j = 0 sind je indizes auf artikel in liste

        esa_distances = zeros((number_articles + 1,number_articles + 1))
        unigram_distances = zeros((number_articles + 1,number_articles + 1))
        #dict mit pointern auf die richtigen zellen im array: artikelId -> zeilen/spaltenindex in matrix
        index_dict = {}
        #zeilen/spaltenindex -> artikelid
        reverse_index_dict = {}
        i = 1


        for articleId in article_dict.keys(): #schreibe einmal an den rand
            esa_distances[i,0] = i #'i-rand' -> Spaltenbeschriftung
            esa_distances[0,i] = i #'j-rand' -> Zeilenbeschriftung
            unigram_distances[i,0] = i
            unigram_distances[0,i] = i
            index_dict[articleId] = i
            # reverse_index_dict[i] = articleId
            i+=1

        #fixme: nur die relevanten vergleiche in die Tabelle schreiben! Nur pro user alle möglichen Kombis
        #annotationList -> dict mit 'probandId':[(artikelId, label),(...),...]
        #Todo hier die labels mit speichern?

        for user in self.annotationList.keys():  #1000 user
            for article_X in self.annotationList[user]: # 30 artikel
                articleIdX = article_X[0]
                article_X = article_dict[articleIdX]
                for article_Y in self.annotationList[user]: # 30 artikel -> 90.000 Vergleiche (besser als alle Artikel mit allen)
                    articleIdY = article_Y[0]
                    article_Y = article_dict[articleIdY]
                    cos_sim_esa = cosine_sim_articles(article_X,article_Y)
                    cos_sim_unigram = cosine_sim_articles(article_X,article_Y,mode=2)
                    if cos_sim_unigram == 0:
                        dist_zero_unigram+=1
                    if cos_sim_esa == 0:
                        dist_zero_esa += 1
                    unigram_distances[index_dict[articleIdX],index_dict[articleIdY]] = cos_sim_unigram
                    esa_distances[index_dict[articleIdX],index_dict[articleIdY]] = cos_sim_esa
                    num_dist_computations += 1

        print "es wurden für Esa und Unigramme je %d Kosinus-Distanzen berechnet. Davon waren bei Esa " \
              "%d = 0 und bei Unigrammen %d = 0" % (num_dist_computations,dist_zero_esa,dist_zero_unigram)

        return unigram_distances,esa_distances,index_dict

    def get_annotators(self):
        return self.annotators

    def get_annotation_list(self):
        return self.annotationList

    def get_author_list(self):
        return self.authorList;

    def get_top_interests(self):
        return self.topInterests

    def create_proband2articles(self,annotation_mode='12_34'):
        probandList = db_connector.get_all_probands()
        allAnnotations = {}
        for proband in probandList:
            probandId = proband[0]
            annotations = db_connector.get_annotations_for_proband(probandId,mode=annotation_mode)
            if len(annotations) > 0:
                allAnnotations[probandId] = annotations
        return allAnnotations

    def create_article_dict(self):
        article_dict = {}
        for proband in proband2articles.keys():
            print "Artikel fuer proband %d werden erstellt" % proband
            for article in proband2articles[proband]:
                articleId = article[0]
                article_dict[articleId] = Artikel(articleId)
                # print proband,articleId, article_dict[articleId].fulltext

        return article_dict

    def create_user_dict(self):
        user_dict = {}
        for proband in proband2articles.keys():
            user_dict[proband] = User(proband)
            print "User fuer proband %d wird erstellt" % proband
        return user_dict

    def get_article_dict(self):
        global article_dict
        return article_dict

    def get_user_dict(self):
        global user_dict
        return user_dict







def normalize_string(string):
        if '(' in string:
            normalizedString = string[0:string.index('(')]
        elif ')' in string:
            normalizedString = string[0:string.index(')')]
        else:
            normalizedString = string

        normalizedString = normalizedString.encode('utf-8').strip().replace('ß','ss')
        # print normalizedString
        return normalizedString.capitalize()

def count_interests(interestList):

    resultInterestList = [[],[]]

    for interest in interestList:

        hobbiesList = re.compile('\\s*,\\s*|\\s*;\\s*').split(interest['hobbies'])
        # hobbiesList = interest['hobbies'].split(', ')

        # print hobbiesList

        for hobby in hobbiesList:
            #teste auf leerheit und ob schon in liste
            if not normalize_string(hobby) in resultInterestList[0] and hobby:
                resultInterestList[0].append(normalize_string(hobby))
                resultInterestList[1].append(1)
            elif hobby:
                resultInterestList[1][resultInterestList[0].index(normalize_string(hobby))] += 1

    result = []

    for x in range(0,len(resultInterestList[0]),1):
        result.append((resultInterestList[0][x],resultInterestList[1][x]))

    return sorted(result, key=operator.itemgetter(1), reverse=True)

def leave_one_out_labels(proband2fvs, probandList, strategy ='article'):

    if strategy == 'article':

        # print 'Fold wird erstellt, für jeden User je 27 train und 3 test'

        #hier will ich liste mit zuordnung: artikelId -> train/test (in/out)
        # Umsetzung: artikel_liste mit artikelId -> bigfoldId

        bigFold = []

        #lolabel für jeden User durchzählen
        for probandId in probandList:
            #i ist das label!
            i = 1
            j = 0

            div = float(len(proband2fvs[probandId]))/10

            for annotation in proband2fvs[probandId]:

                bigFold.append(i)
                j+=1
                if(j>=div):
                    i+=1
                    j=0

        return bigFold

    elif strategy == 'user':

        print 'Fold wird erstellt, User 9:1 train/test'

        bigFold = []

        #deswegen sollten min 10 user zum testen genutzt werden ;)
        div =  float(len(probandList)) / 10

        i = 1
        j = 0
        for probandId in probandList:
            j+=1
            for annotation in proband2fvs[probandId]:
                bigFold.append(i)
            if(j>=div):
                i+=1
                j=0

        return bigFold

def clean_author_list(authorList):
        result = []
        if authorList:
            tagger = stanford_postagger.StanfordPOSTagger('/Users/Fabian/PycharmProjects/nw-classification/tagging/taggers/german-fast.tagger', '/Users/Fabian/PycharmProjects/nw-classification/tagging/stanford-postagger-full-2015-04-20/stanford-postagger-3.5.2.jar')
            for author in authorList:
                tokens = nltk.word_tokenize(author)
                tagged = tagger.tag(tokens)
                tmp = ""
                for word, tag in tagged:
                    if tag == 'NE':
                        tmp += (" " + word)
                if tmp:
                    result.append(tmp.lower().strip().encode('utf-8'))

        return result

def tag_word_list(list):
    result = []
    if list:
        tagger = stanford_postagger.StanfordPOSTagger('/Users/Fabian/PycharmProjects/nw-classification/tagging/taggers/german-fast.tagger', '/Users/Fabian/PycharmProjects/nw-classification/tagging/stanford-postagger-full-2015-04-20/stanford-postagger-3.5.2.jar')
        for word in list:
            tagged = tagger.tag(word)
            result.append(tagged)
    return result

def ESA_compare(artikelId, probandId, numberArticles):

        esa_artikel = article_dict[artikelId].esa_vec_normalized
        esa_proband = user_dict[probandId].esa_vec_normalized

        similarity = vector_similarty(esa_artikel,esa_proband)

        # result_normalized_e10 = 0
        #
        # if similarity < 0.0000001:
        #     result_normalized = 0
        # elif similarity < 0.000001:
        #     result_normalized = 1
        # elif similarity < 0.00001:
        #     result_normalized = 2
        # elif similarity < 0.0001:
        #     result_normalized = 3
        # elif similarity < 0.001:
        #     result_normalized = 4
        # elif similarity < 0.01:
        #     result_normalized = 5
        # elif similarity < 0.1:
        #     result_normalized = 6
        # elif similarity < 1.0:
        #     result_normalized = 7
        # # elif similarity < 0.009:
        # #     result_normalized = 8
        # # else:
        # #     result_normalized = 9
        #
        # result_normalized_0001 = 0
        # if similarity < 0.0001:
        #     result_normalized_0001 = 0
        # elif similarity < 0.0002:
        #     result_normalized_0001 = 1
        # elif similarity < 0.0003:
        #     result_normalized_0001 = 2
        # elif similarity < 0.0004:
        #     result_normalized_0001 = 3
        # elif similarity < 0.0005:
        #     result_normalized_0001 = 4
        # elif similarity < 0.0006:
        #     result_normalized_0001 = 5
        # elif similarity < 0.0007:
        #     result_normalized_0001 = 6
        # elif similarity < 0.0008:
        #     result_normalized_0001 = 7
        #
        # result_normalized_001 = 0
        # if similarity < 0.001:
        #     result_normalized_001 = 0
        # elif similarity < 0.002:
        #     result_normalized_001 = 1
        # elif similarity < 0.003:
        #     result_normalized_001 = 2
        # elif similarity < 0.004:
        #     result_normalized_001 = 3
        # elif similarity < 0.005:
        #     result_normalized_001 = 4
        # elif similarity < 0.006:
        #     result_normalized_001 = 5
        # elif similarity < 0.007:
        #     result_normalized_001 = 6
        # elif similarity < 0.008:
        #     result_normalized_001 = 7

        return similarity

def vector_similarty(vec1,vec2):

    enumerator = 0.0
    denom_1 = 0.0
    denom_2 = 0.0

    # used_keys = []

    for key in vec1.keys(): #für alle einträge in vec1
        #zuerst alle keys
        if key in vec2:     #falls eintrag auch in vec2
            enumerator += float(vec1[key]) * float(vec2[key])       #zähler +=  (a_i*b_i)
        denom_1 += float(vec1[key])**2      #summe nenner der ai += a_i^2
    for key in vec2.keys(): #für alle eintrage vec2
        denom_2 += float(vec2[key])**2      #summe nenner der ai += a_i^2

    denom = np.sqrt(denom_1) * np.sqrt(denom_2)     #finalen nenner ausrechnen

    if denom == 0:
        file_util.write("Nenner = 0!",'error')
        # print "Nenner = 0! -> %f" % denom
        cosine_sim = 0.0
    else:
        # print enumerator,denom
        cosine_sim = float(enumerator) / float(denom)

    if cosine_sim < -1 or cosine_sim > 1:
        file_util.write("Kosinus falsch definiert (<-1 oder >1) -> %f" % cosine_sim,'error')
    return cosine_sim

def cosine_sim_articles(article_1,article_2,mode = 4):
    vec1 = {}
    vec2 = {}
    if mode == 1:
        vec1 = article_1.bow
        vec2 = article_2.bow
    elif mode == 2:
        vec1 = article_1.bow_filtered
        vec2 = article_2.bow_filtered
    elif mode == 3:
        vec1 = article_1.bow_bigrams
        vec2 = article_2.bow_bigrams
    elif mode == 4:
        vec1 = article_1.esa_vec
        vec2 = article_2.esa_vec
    result = vector_similarty(vec1,vec2)
    return result


def compare_esa_topics(topic_dict_1, topic_dict_2):
    #soll ein dict mit binären features zurückgeben: falls topic in beiden : 1/0
    result = 0
    for topic in topic_dict_1.keys():
        if topic in topic_dict_2.keys():
            result = 1
    return result

def normalize_esa_vector(esa_vec_dict):
    #normalize by biggest value in vector: leicht sinnvollere Ergebnisse, aber nicht vergleichbar mit anderen Esa-Vektoren
    result = esa_vec_dict
    if result:
        max_value = np.max(esa_vec_dict.values())
        result = {}
        for key in esa_vec_dict.keys():
            result[key] = float(esa_vec_dict[key])/max_value
    return result