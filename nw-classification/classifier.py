# -*- coding: utf-8 -*-


from sklearn import svm, cross_validation, tree
from sklearn.naive_bayes import MultinomialNB
import classification_util
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn import metrics
import numpy as np
import codecs
import file_util
import copy
import scipy.sparse as sp

#todo: kosinus vergleich überprüfen
#todo: esa-schwellwert (durchschnitt) pro user und pro artikel. Dann die Topics darüber genauer anschauen.
    # 1. vgl top topics esa-interessen-vektor mit top topics artikel vektor
    # 2. vgl top topics esa-vektor basierend auf bisher bewerteten artikeln mit top topics artikel vektor

#-> je EIN binäres feature für esa_esa oder interest_esa

#Frage an Experten: unterschied unigramme,BOW



esa_features = ['esa_mean_positives','esa_min_positives','esa_max_positives','esa_mean_negatives','esa_min_negatives','esa_max_negatives','interest_esa_topic_comparison']
unigram_features = ['unigram_mean_positives','unigram_min_positives','unigram_max_positives','unigram_mean_negatives','unigram_min_negatives','unigram_max_negatives']
dynamic_features = esa_features + unigram_features

def perform_cross_validation(fv, esa_dynamic_folds, lv, fv2artikelId,
                             annotator_list, feature_list, lol,
                             clf_choice='svm', fold_mode = 'article',
                             predict = False, C=10, dynamic=True,
                             output_mode = 'output'):

    if not fv:
        msg = "feature vektor ist leer!"
        print msg
        file_util.write(msg,mode=output_mode)


    try:
        train_with = "Training mit: %s" % feature_list
        print train_with
        file_util.write(train_with + "\n",mode=output_mode)

        vec = DictVectorizer()
        tfidf = TfidfTransformer()

        if clf_choice == 'svm_linear':
            clf = svm.SVC(kernel='linear', C=C)
        elif clf_choice == 'svm_rbf':
            clf = svm.SVC(kernel='rbf', C=C)
        elif clf_choice == 'svm_poly':
            clf = svm.SVC(kernel='poly', C=C)
        elif clf_choice == 'decision_tree':
            clf = tree.DecisionTreeClassifier()
        elif clf_choice == 'mn_naive_bayes':
            clf = MultinomialNB()


        X = vec.fit_transform(fv).toarray()
        # X_tfidf = tfidf.fit_transform(X).toarray()
        y = np.array(lv)

        scores = []

        esa_feature_list = []
        unigram_feature_list = []
        for feature in feature_list:
            if 'esa' in feature:
                esa_feature_list.append(feature)
            elif 'unigram' in feature:
                unigram_feature_list.append(feature)

        # clf.fit(X,y)
        #
        # clf.predict(X)


        if not predict:
            for metric in ["precision", "recall", "f1", "accuracy"]:
                if dynamic:
                    scores.append(dynamic_cross_val_score(clf,fv,esa_feature_list,unigram_feature_list,esa_dynamic_folds,y, cv=lol, scoring=metric).mean())
                else:
                    scores.append(cross_validation.cross_val_score(clf, X, y, cv=lol, scoring=metric).mean())


            predicted = []
            #auch predict umbasteln!
            if dynamic:
                predicted = dynamic_cross_val_predict(clf,fv,esa_feature_list,unigram_feature_list,esa_dynamic_folds, y, cv=lol)
            else:
                predicted = cross_validation.cross_val_predict(clf, X, y, cv=lol)



            result = ("Ergebnis:\tP=%0.2f\tR=%0.2f\tF1=%0.2f\t\tAcc=%0.2f"%(scores[0], scores[1], scores[2], scores[3]))
            conf_mat = "%s\n" % metrics.confusion_matrix(y,predicted)
            file_util.write(conf_mat,mode=output_mode)
            file_util.write(result + "\n",mode=output_mode)
            print result
            print conf_mat

            return (scores[0], scores[1], scores[2], scores[3])

        # if predict:
        #     fp_list = []
        #     predicted = cross_validation.cross_val_predict(clf, X_tfidf, y, cv=lol)
        #     for i in range(len(predicted)):
        #         #finde alle false positives
        #         if y[i] == -1 and predicted[i] == 1:
        #             fp_list.append((fv2artikelId[i],i,y[i],predicted[i]))
        #     print "accuracy per predict:",metrics.accuracy_score(y, predicted)
        #     return fp_list, metrics.confusion_matrix(y,predicted)

    except ValueError as e:
            print e
            if not predict:
                return (0.0,0.0,0.0,0.0)
            else:
                return [], metrics.confusion_matrix([],[])


def dynamic_cross_val_score(estimator, fv, esa_feature_list, unigram_feature_list, dynamic_X, y=None, scoring=None, cv=None,
                verbose=0, fit_params=None):

    print "dynamic cross val mit %s" % esa_feature_list + unigram_feature_list
    vec = DictVectorizer()
    tfidf = TfidfTransformer()

    X = vec.fit_transform(fv).toarray()
    # X= tfidf.fit_transform(X).toarray()

    X, y = cross_validation.indexable(X, y)

    cv = cross_validation.check_cv(cv, X, y, classifier=cross_validation.is_classifier(estimator))
    scorer = cross_validation.check_scoring(estimator, scoring=scoring)
    scores = []

    cross_val_step = 0
    for train, test in cv:

        fv_copy = copy.deepcopy(fv)

        #baue X in jedem Schritt neu
        for i in range(0,len(fv)): #jedes i steht für einen featuredict
            feature_dict = fv_copy[i]
            dynamic_vec = dynamic_X[cross_val_step] #zeigt auf esa_vec
            for feature in esa_feature_list:
                feature_dict.update(dynamic_vec[find_index_for_dynamic_feature(feature)][i]) #das i-te feature-dict mit esa-feature updaten
            for feature in unigram_feature_list:
                feature_dict.update(dynamic_vec[find_index_for_dynamic_feature(feature)][i]) #das i-te feature-dict mit esa-feature updaten



        X = vec.fit_transform(fv_copy).toarray()
        # X = tfidf.fit_transform(X).toarray()

        scores.append(cross_validation._fit_and_score(cross_validation.clone(estimator), X, y, scorer,
                        train, test, verbose, None, fit_params))

        cross_val_step += 1


    return np.array(scores)[:, 0]

def dynamic_cross_val_predict(estimator, fv, esa_feature_list, unigram_feature_list, dynamic_X, y=None, cv=None,
                              verbose=0, fit_params=None):


    print "dynamic predict cross val mit %s" % esa_feature_list + unigram_feature_list


    vec = DictVectorizer()
    tfidf = TfidfTransformer()

    X = vec.fit_transform(fv).toarray()
    # X = tfidf.fit_transform(X).toarray()

    X, y = cross_validation.indexable(X, y)
    cv = cross_validation.check_cv(cv, X, y, classifier=cross_validation.is_classifier(estimator))

    preds_blocks = []

    cross_val_step = 0
    for train, test in cv:

        fv_copy = copy.deepcopy(fv)

        #baue X in jedem Schritt neu
        for i in range(0,len(fv)): #jedes i steht für einen featuredict
            feature_dict = fv_copy[i]
            dynamic_vec = dynamic_X[cross_val_step] #zeigt auf esa_vec
            for feature in esa_feature_list:
                feature_dict.update(dynamic_vec[find_index_for_dynamic_feature(feature)][i]) #das i-te feature-dict mit esa-feature updaten
            for feature in unigram_feature_list:
                feature_dict.update(dynamic_vec[find_index_for_dynamic_feature(feature)][i]) #das i-te feature-dict mit esa-feature updaten


        X = vec.fit_transform(fv_copy).toarray()
        # X = tfidf.fit_transform(X).toarray()

        preds_blocks.append(cross_validation._fit_and_predict(cross_validation.clone(estimator), X, y,
                                                      train, test, verbose,
                                                      fit_params))

        cross_val_step+=1

    preds = [p for p, _ in preds_blocks]
    locs = np.concatenate([loc for _, loc in preds_blocks])
    if not cross_validation._check_is_partition(locs, cross_validation._num_samples(X)):
        raise ValueError('cross_val_predict only works for partitions')
    inv_locs = np.empty(len(locs), dtype=int)
    inv_locs[locs] = np.arange(len(locs))

    # Check for sparse predictions
    if sp.issparse(preds[0]):
        preds = sp.vstack(preds, format=preds[0].format)
    else:
        preds = np.concatenate(preds)
    return preds[inv_locs]



def find_index_for_dynamic_feature(feature):
    return dynamic_features.index(feature)