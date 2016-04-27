# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt
import file_util

#bekommt feature matrix und f2matrix
#macht wunderschoene grafiken

colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']

def print_examples(featureMatrix,f2matrix,num_examples):
    f2matrix = {}
    for key in f2matrix.keys():
        filename = key + '_bsp.txt'
        title = "Feature: " + key + "\n"
        number_of_single_features = "Anzahl and Einzelfeatures des Features: %d\n" % len(featureMatrix[f2matrix[key]][0].keys())
        file_util.write(title,'analysis',filename)
        file_util.write(number_of_single_features,'analysis',filename)
        for i in range(0,num_examples):
            example = "Beispiel %d:\n\t%s\n" % (i,featureMatrix[f2matrix[key]][i])
            file_util.write(example,'analysis',filename)

def create_interest_graphic(featureMatrix,f2matrix):
    keys = ['title_interests','text_interests','user_titel_interests','user_text_interests']

    #zähle vorkommenshäufigkeit
    for key in keys:
        ones = 0
        zeros = 0
        count = 0
        for article_vect in featureMatrix[f2matrix[key]]:
            dict_values = article_vect[0].values()
            if 1 in dict_values:
                ones+=1
            elif 0 in dict_values:
                zeros+=1
            count+=1

        sizes = [float(ones)/count,float(zeros)/count]
        plt.pie(sizes, labels=['Interesse kommt in Titel vor','Interesse kommt nicht vor'], colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
        plt.title('Verteilung des Features: ' + key)
        plt.axis('equal')
        plt.savefig(file_util.ana_dir + key + '.png')

def create_author_graphic(featureMatrix,f2matrix):
    counting_dict = featureMatrix[f2matrix['author']][0]
    for key in counting_dict.keys():
        counting_dict[key] = 0
    for article_feature_dict in featureMatrix[f2matrix['author']]:
        for key in article_feature_dict.keys():
            if article_feature_dict[key] == 1:
                counting_dict[key] += 1

    labels = []
    sizes = []
    for key in counting_dict.keys():
        labels.append(key)
        sizes.append(counting_dict[key])


    plt.pie(sizes, labels=labels, colors=colors,
            autopct='%1.1f%%', shadow=True, startangle=90)
    plt.title('Verteilung des Features: ' + 'author')
    plt.axis('equal')
    plt.savefig(file_util.ana_dir + 'author' + '.png')

def create_ressort_graphic():
    pass

def create_word_count_graphic():
    pass

def create_page_normalized_graphic():
    pass

def create_esa_graphic():
    pass

def perform_overall_analysis(featureMatrix,f2matrix):
    print_examples(featureMatrix,f2matrix,num_examples=3)
    create_interest_graphic(featureMatrix,f2matrix)
    create_author_graphic(featureMatrix,f2matrix)
    pass