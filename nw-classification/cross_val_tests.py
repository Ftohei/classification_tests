# -*- coding: utf-8 -*-


__author__ = 'Fabian'

import classifier
import operator
import codecs
import time
import classification_util
import file_util
import feature_analysis

prec = []
rec = []
f1 = []
acc = []


def normal_cross_val(featurelist,fold_method,C_list,clf_choice):
    # result = classifier.perform_cross_validation(fv,lv,proband2fvs,fv2artikelId, probandList, feature, fold_mode=method,C=c)
    # was soll die funktion tun? erst alle features einzeln testen, danach alle gemeinsam

    for feature in featurelist:
        dynamic_features = False
        if 'esa' in feature or 'unigram' in feature:
                dynamic_features = True
        else:
            fv = fMatrix[f2matrix[feature]]

        for c in C_list:
            result = classifier.perform_cross_validation(fv, dynamic_folds, lv,
                                                         fv2artikelId,
                                                         probandList, [feature], lol,
                                                         clf_choice, fold_mode=fold_method,
                                                         C=c, dynamic=dynamic_features)

        prec.append((feature,result[0]))
        rec.append((feature,result[1]))
        f1.append((feature,result[2]))
        acc.append((feature,result[3]))

    fv = []
    dynamic_features = False

    for i in range(0,len(fMatrix[0])):
        dict = {}
        for feature in featurelist:
            if 'esa' in feature or 'unigram' in feature:
                dynamic_features = True
            else:
                dict.update(fMatrix[f2matrix[feature]][i])
        fv.append(dict)

    file_util.write("evaliere alle Features gemeinsam...\n")
    file_util.write("Anzahl features = %d" % len(fv[0].keys()))


    print "\n\nevaluiere alle features gemeinsam...\n"

    classifier.perform_cross_validation(fv, dynamic_folds, lv,
                                                 fv2artikelId,
                                                 probandList, featurelist, lol,
                                                 clf_choice, fold_mode = fold_method,
                                                 dynamic=dynamic_features)

def predict_cross_val(featurelist,fold_method,fv2userId,clf_choice):

    print "\n\nevaluiere einzelne Features per predict...\n"

    for feature in featurelist:
        if not (feature == 'yes_no'):
            fv = []
            pred_file = ('pred_%s.txt' % feature)
            for i in range(0,len(fMatrix[0])):
                dict = {}
                dict.update(fMatrix[f2matrix[feature]][i])
                fv.append(dict)
            fp_list,confusion_matrix = classifier.perform_cross_validation(fv,lv,proband2fvs,fv2artikelId, probandList, [feature], clf_choice,
                                                          fold_mode = fold_method, predict=True)


            print "Confusion_matrix:\n",confusion_matrix

            for artikelId, fp_fv_index, target, pred in fp_list:
                print artikelId, fv2artikelId[fp_fv_index], fp_fv_index, target, pred,
                # article = nwAnnotations.get_article_dict(fv2artikelId[fp_fv_index])
                article = nwAnnotations.get_article_dict()[artikelId]
                user = nwAnnotations.get_user_dict()[fv2userId[fp_fv_index]]
                complete_feature = fMatrix[f2matrix[feature]][fp_fv_index]
                output = "%s:\n\t%s\t -> Target : %d\t Label : %d\nFertiges Feature : %s" % (article.id, article.title, target, pred, complete_feature)
                if feature == 'user_titel_interests':
                    # pass
                    output = "%s:\n\t%s\t -> Target : %d\t Label : %d\n" \
                             "Interessen: %s\n" \
                             "Fertiges Feature: %s" % (article.id, article.title, target, pred, user.get_interests(),complete_feature)
                    #id, titel, interessen, target, pred, fertiges feature
                elif feature == 'user_text_interests':
                    output = "%s:\n\t%s\t -> Target : %d\t Label : %d\n" \
                             "Text: %s\n" \
                             "Interessen: %s\n" \
                             "Fertiges Feature: %s" % (article.id, article.title, target, pred, article.fulltext, user.get_interests(),complete_feature)
                    #id, titel text, interessen, target, pred, fertiges feature
                elif feature == 'esa_comparison_1000_0001':
                    esa_vec1 = article.esa_vec
                    article_esa = []
                    esa_vec2 = user.esa_vec
                    user_esa = []
                    sim_esa = []
                    for key in esa_vec1.keys():
                        if esa_vec1[key] > 0.0:
                            article_esa.append((key,esa_vec1[key]))
                            if key in esa_vec2 and esa_vec2[key] > 0.0:
                                sim_esa.append((key,esa_vec1[key],esa_vec2[key]))
                    for key in esa_vec2.keys():
                        if esa_vec2[key] > 0.0:
                            user_esa.append((key,esa_vec2[key]))

                    output = "%s:\n\t%s\t -> Target : %d\t Label : %d\n" \
                             "Text: %s\n" \
                             "Interessen: %s\n" \
                             "Esa-Vektor Text: %s\n" \
                             "Esa-Vektor Interessen: %s\n" \
                             "Gemeinsame ESA-Elemente : %s\n" \
                             "Fertiges Feature: %s\n" % (article.id, article.title, target, pred, article.fulltext, user.get_interests(), article_esa, user_esa, sim_esa, complete_feature)

                print output
                file_util.write(output,'pred',pred_file)

def ablation_regime(featurelist, clf_choice):
    write_mode = 'ablation'
    string = "Berechne Ablation-Regime"
    print string
    file_util.write(string,write_mode)


    for i in range(0,len(featurelist)):     #so viele Ablation-durchgänge, wie man features hat
        #Ablauf Ablation:
        #   1. starte mit X features. Berechne mit Cross-Validation scores. Speichere die



        current_features = list(featurelist)

        dynamic_features = False
        for feature in current_features:
            if 'esa' in feature or 'unigram' in feature:
                dynamic_features = True

        fv = []                                 # setze feature-vektor zusammen
        for i in range(0,len(fMatrix[0])):      # für alle feature-vektoren
            dict = {}
            for single_feature in current_features:         # für alle features in der featureliste
                if 'esa' not in single_feature and 'unigram' not in single_feature:    # falls das feature kein dynamisches Feature ist
                    dict.update(fMatrix[f2matrix[single_feature]][i])          #füge feature in den feature-vektor mit ein
            fv.append(dict)                     # schreibe den feature-vektor in die liste der feature-vektoren

        #führe cross-validation durch
        current_prec, current_rec, current_f1, current_acc = classifier.perform_cross_validation(fv, dynamic_folds, lv,
                                            fv2artikelId, probandList, current_features, lol,
                                            clf_choice, fold_mode = cross_eval_methods[0],
                                            dynamic=dynamic_features,
                                            output_mode='ablation')

        # string = "Aktueller Stand: %s\n\tP=%0.2f\tR=%0.2f\tF1=%0.2f\t\tAcc=%0.2f" % (current_features,current_prec,current_rec,current_f1,current_acc)

        #liste mit tupeln: je name des features und differenz vom current_f1-score
        f1_differences = []

        for feature in current_features:
            #   2. iteriere über alle features: lasse je ein feature weg, speichere die scores.
            string = "Entferne Testweise %s" % feature
            print string
            file_util.write(string,write_mode)

            tmp_features = list(current_features)
            tmp_features.remove(feature)



            dynamic_features = False
            for feature in tmp_features:
                if 'esa' in feature or 'unigram' in feature:
                    dynamic_features = True

            fv = []                                 # setze feature-vektor zusammen
            for i in range(0,len(fMatrix[0])):      # für alle feature-vektoren
                dict = {}
                for single_feature in tmp_features:         # für alle features in der featureliste
                    if 'esa' not in single_feature and 'unigram' not in single_feature:    # falls das feature kein dynamisches Feature ist
                        dict.update(fMatrix[f2matrix[single_feature]][i])          #füge feature in den feature-vektor mit ein
                fv.append(dict)                     # schreibe den feature-vektor in die liste der feature-vektoren

            #führe cross-validation durch
            prec, rec, f1, acc = classifier.perform_cross_validation(fv, dynamic_folds, lv,
                                                fv2artikelId, probandList, tmp_features, lol,
                                                clf_choice, fold_mode = cross_eval_methods[0],
                                                dynamic=dynamic_features,
                                                output_mode='ablation')

            #   3. berechne, welches feature den größten einbruch in der performance erzeugt
            f1_difference = current_f1 - f1
            f1_differences.append((feature, f1_difference))

        sorted_differences = sorted(f1_differences, key=lambda x: x[1], reverse=True)

        string = "\n-----------Entferne endgueltig bestes Feature(nach F1): %s mit einer F1-Differenz von %d Prozent------------\n" % (feature,sorted_differences[0][1])
        print string
        file_util.write(string,mode=write_mode)
        featurelist.remove(sorted_differences[0][0]) #entferne das feature mit dem stärksten einbruch





def del_scores():
    prec = []
    rec = []
    f1 = []
    acc = []






all_features_with_nonbinaries = ['title_interests','text_interests', 'ressort_prior', 'ressort_specific','ressort_specific_rating', 'author', 'page_normalized', 'word_count_text_normalized',
                'word_count_titel', 'user_titel_interests', 'user_text_interests',
                'comparison_1000_0001','cf_age_ressort','cf_sex_ressort','cf_edu_ressort','cf_age_page',
                'cf_sex_page','cf_edu_page','cf_age_word_count_text','cf_sex_word_count_text','cf_edu_word_count_text',
                'esa_mean_positives','esa_min_positives','esa_max_positives','esa_mean_negatives','esa_min_negatives','esa_max_negatives',
                'unigram_mean_positives','unigram_min_positives','unigram_max_positives','unigram_mean_negatives','unigram_min_negatives','unigram_max_negatives',
                'interest_esa_topic_comparison'
                ]

all_features = ['title_interests','text_interests', 'ressort_prior', 'ressort_specific','ressort_specific_rating', 'author',
                'user_titel_interests', 'user_text_interests',
                'comparison_1000_0001','cf_age_ressort','cf_sex_ressort','cf_edu_ressort','cf_age_page',
                'cf_sex_page','cf_edu_page','cf_age_word_count_text','cf_sex_word_count_text','cf_edu_word_count_text',
                'esa_mean_positives','esa_min_positives','esa_max_positives','esa_mean_negatives','esa_min_negatives','esa_max_negatives',
                'unigram_mean_positives','unigram_min_positives','unigram_max_positives','unigram_mean_negatives','unigram_min_negatives','unigram_max_negatives',
                'interest_topic_comparison'
                ]

all_nondynamic_features_no_binaries = [
                'title_interests','text_interests', 'ressort_prior', 'ressort_specific','ressort_specific_rating', 'author',
                'user_titel_interests', 'user_text_interests',
                'comparison_1000_0001','cf_age_ressort','cf_sex_ressort','cf_edu_ressort','cf_age_page',
                'cf_sex_page','cf_edu_page','cf_age_word_count_text','cf_sex_word_count_text','cf_edu_word_count_text',
                ]

feature_configs = [all_nondynamic_features_no_binaries, all_features, all_features_with_nonbinaries]

def eval_metrics(metrics):


    print "\n\nAufstellung Ergebnisse sortiert nach Metriken:\n"

    for metric in [('Precision',0),('Recall',1),('F1',2),('Accuracy',3)]:
        string = "%s" % metric[0]
        print string
        file_util.write(string)
        for elem in sorted(metrics[metric[1]], key=operator.itemgetter(1), reverse=True):
            metric = "\t%s : \t\t\t%2.4f" % (elem[0],elem[1])
            print metric
            file_util.write(metric)

cross_eval_methods = ['article', 'user']
c_metaparams = [10]
clf_list = ['svm_linear','svm_rbf','svm_poly','decision_tree','mn_naive_bayes']

start_time = time.time()

nwAnnotations = classification_util.NwAnnotations(annotation_mode='1_4')

#einstellungen: dynamische features an/aus, welche annotationen werden genommen? wie groß soll der esa-vektor pro artikel/user sein?
fMatrix, dynamic_folds, f2matrix, lv, proband2fvs, fv2artikelId, fv2userId, probandList, lol = nwAnnotations.create_feature_matrix(dynamic=False)

# feature_analysis.perform_overall_analysis(fMatrix,f2matrix)
# feature_analysis.print_examples(fMatrix,f2matrix,5)

for clf_choice in clf_list[0:3]:
    for feature_config in [all_nondynamic_features_no_binaries]:

        string = "\n------------------TESTS MIT %s-------------\n" % clf_choice.upper()
        print string
        file_util.write(string)

        normal_cross_val(all_nondynamic_features_no_binaries, cross_eval_methods[0], c_metaparams, clf_choice)

        # ablation_regime(featurelist,clf_choice)

        del_scores()

computation_time = ("--- %s seconds ---" % (time.time() - start_time))
file_util.write(computation_time)
print computation_time



