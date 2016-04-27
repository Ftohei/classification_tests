#der Mülleimer

    def to_general_feature_vec(self, probandId, featureList):
        #deprecated
        featureVector = []
        labelVector = []
        fv2txt = {}
        i = 0
        for annotation in self.annotationList[probandId]:

            artikelId = annotation[0]
            label = annotation[1]
            text = Artikel(artikelId)
            #titel und text in einen topf geschmissen
            # featureDict = text.compareTextAndTitleToInterests(self.topInterests)

            featureDict = {}


            if 'interessen_text' in featureList:
                featureDict.update(text.compareTitleToInterests(self.topInterests))

            if 'interessen_titel' in featureList:
                featureDict.update(text.compareTextToInterests(self.topInterests))

            if 'ressorts' in featureList:
                ressortDict = text.compareRessortToRessortRatings(probandId)
                featureDict.update(ressortDict)

            if 'autor' in featureList:
                #momentan binäres feature: hat autor oder nicht
                if text.author:
                    featureDict['artikel_autor'] = 1
                else:
                    featureDict['artikel_autor'] = 0

            if 'artikel_seite' in featureList:
                featureDict['artikel_seite'] = text.page

            #todo stopwords filtern, um feature präziser zu machen?

            if 'word_count_text' in featureList:
                featureDict['word_count_text'] = text.wordCountText

            if 'word_count_titel' in featureList:
                featureDict['word_count_titel'] = text.wordCountTitle

            #infos über proband
            if 'infos_proband' in featureList:
                basic_probandInfo = db_connector.get_age_edu_sex_for_probandId(probandId)

                featureDict['proband_alter'] = basic_probandInfo[0]
                if basic_probandInfo[2][0] == 'M':
                    featureDict['proband_geschlecht'] = 1
                else:
                    featureDict['proband_geschlecht'] = 0

                if basic_probandInfo[1][0] == 'M':
                    featureDict['proband_bildung'] = 1
                elif basic_probandInfo[1][0] == 'A':
                    featureDict['proband_bildung'] = 2
                elif basic_probandInfo[1][0] == 'H':
                    featureDict['proband_bildung'] = 3
                else:
                    featureDict['proband_bildung'] = 0

            featureVector.append(featureDict)
            labelVector.append(int(label))

            fv2txt[i]=artikelId
            i += 1


        if self.checkClassSize(labelVector):
            return (featureVector, labelVector, fv2txt)
        else:
            # print "% 20s\tZu wenige Instanzen in einer Klasse (min 10)" % (probandId)
            return False

    def toFeatureVectors(self, probandId, binary=False):
        featureVector = []
        labelVector = []
        fv2txt = {}
        i = 0
        for annotation in self.annotationList[probandId]:
            artikelId = annotation[0]
            label = annotation[1]
            text = Artikel(artikelId)
            features = ["TITLE_%s"%tt for tt in text.getTitleTokens()]
            features.extend([tt for tt in text.getTitleTokens()])
            features.extend(text.getUnigrams())
            instanceDict = {}
            for feature in features:
                if binary:
                    instanceDict[feature] = 1
                else:
                    instanceDict[feature] = instanceDict.setdefault(feature, 0)+1
            featureVector.append(instanceDict)
            fv2txt[i]=artikelId
            i += 1
            if label != "-1":
                labelVector.append(int(label))

        if self.checkClassSize(labelVector):
            return (featureVector, labelVector, fv2txt)
        else:
            print "% 20s\tZu wenige Instanzen in einer Klasse (min 10)" % (probandId)
            return False

    def compareTextAndTitleToInterests(self, interestList):
        feature = {}
        for interest in interestList:
            if type(interest) == tuple:
                interest = interest[0]
            feature[interest] = 0
            for word in re.split("\W", self.fulltext):
                if (interest.lower().decode('utf-8')) == (word.lower().decode('utf-8')):
                    feature[interest] = 1
            for word in re.split("\W", self.title):
                if (interest.lower().decode('utf-8')) == (word.lower().decode('utf-8')):
                    feature[interest] = 1

        return feature

    def compute_interest_cross_feats(self, user):

        cross_features = {}

        cross_features_age = {}
        cross_features_sex = {}
        cross_features_edu = {}


        for interest in self.topInterests:
            interest = interest[0]

            if interest in user.get_interests():

                for age in age_groups:
                    feature = "%s_%s" % (interest,age)
                    if user.normalized_age == age:
                        cross_features_age[feature] = 1
                    else:
                        cross_features_age[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (interest,sex)
                    if user.sex == age:
                        cross_features_sex[feature] = 1
                    else:
                        cross_features_sex[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (interest,edu)
                    if user.edu == edu:
                        cross_features_edu[feature] = 1
                    else:
                        cross_features_edu[feature] = 0

            else:

                for age in age_groups:
                    feature = "%s_%s" % (interest,age)
                    cross_features_age[feature] = 0
                for sex in sexes:
                    feature = "%s_%s" % (interest,sex)
                    cross_features_sex[feature] = 0
                for edu in edus:
                    feature = "%s_%s" % (interest,edu)
                    cross_features_edu[feature] = 0

        cross_features.update(cross_features_age)
        cross_features.update(cross_features_edu)
        cross_features.update(cross_features_sex)

        return cross_features

 # print "evaluiere alle features einzeln...\n\n"
    #
    # for feature in all_features:
    #
    #     feature_list = [feature]
    #
    #     fv,lv,proband2fvs,fv2artikelId,probandList = nwAnnotations.general_feature_vectors(feature_list)
    #
    #     scores = classifier.perform_cross_validation(fv, lv, proband2fvs, fv2artikelId, probandList, feature_list, True, method)
    #
    #     #speichere feature_list und accuracy
    #     fv_list_w_acc.append((feature_list, scores[3]))
    #
    #     print "\n\n\n-------------------\n\n\n"
    #
    #
    # fl2accuracy  = []
    #
    # for item in fv_list_w_acc:
    #     if item[1] > 0.6:
    #         fl2accuracy.append(item)
    #
    # fl2accuracy.sort(key=operator.itemgetter(1))
    #
    # feature_list = [feature[0] for feature in fl2accuracy[:5] ]
    #
    # print "evaluiere die besten features gemeinsam...\n\n"
    #
    # fv,lv,proband2fvs,fv2artikelId, probandList = nwAnnotations.general_feature_vectors(feature_list)
    #
    # scores = classifier.perform_cross_validation(fv, lv, proband2fvs, fv2artikelId, probandList, feature_list, True, method)
    #
    # print "\n\n\n-------------------\n\n\n"


####TODO wichtig, behalten!!!


    # nwAnnotations = classification_util.NwAnnotations()

# vec = DictVectorizer()
# tfidf = TfidfTransformer()
# clf = svm.SVC(kernel='linear', C=10)
#
# fv_user, lv_user, proband2fvs_user, fv2artikelId_user, probandList_user = nwAnnotations.general_feature_vectors(all_features, user_specific=True)
# X = vec.fit_transform(fv_user).toarray()
# X_tfidf = tfidf.fit_transform(X).toarray()
# y = np.array(lv_user)
#
# lol_labels = classification_util.leave_one_out_labels(proband2fvs_user, nwAnnotations.get_annotators(), 'article')
# lol = cross_validation.LeaveOneLabelOut(lol_labels)
#
# for train_fold, test_fold in lol:
#     X_train, X_test = [X_tfidf[i] for i in train_fold], [X_tfidf[i] for i in test_fold]
#     y_train, y_test = [y[i] for i in train_fold], [y[i] for i in test_fold]
#     clf.fit(X_train, y_train)
#     y_pred = clf.predict(X_test)
#     dist_y = clf.decision_function(X_test)
#     pred_dist_pairs = zip(y_pred, dist_y)
#     for i in range(len(test_fold)):
#         if y_pred[i] == 1:
#             for pos_inst in [(fv2artikelId_user[test_fold[i]], dist_y[i])]:
#                 pos_instances.append((pos_inst, 1))
#                 # print pos_inst
#         if y_pred[i] == (-1):
#             for neg_inst in [(fv2artikelId_user[test_fold[i]], dist_y[i])]:
#                 neg_instances.append((neg_inst, -1))
#                 # print pos_inst
#         # for txt, dist in sorted(pos_instances, key=lambda x: x[1], reverse=True)[:10]:
#             # print txt, dist
#
#         # print "Anzahl korrekter Vorhersagen: %d von 30" % count_correct_predictions(nwAnnotations.get_annotation_list()[probandId],pos_instances)
#
#     correct_preds.append(count_correct_predictions(nwAnnotations.get_annotation_list(),pos_instances))
#
# print "Positive Klassifikationen: %s" % pos_instances
# print "Negative Klassifikationen: %s" % neg_instances
#
# print "Korrekte Klassifikationen: %d" % (correct_preds[0])



    # # for proband in testProbands:
    #     probandId = proband[0]
    #     featureVectors = nwAnnotations.to_general_feature_vec(probandId, featureList)
    #     if(featureVectors != False):
    #         (fv, lv, fv2txt) = featureVectors
    #         X = vec.fit_transform(fv).toarray()
    #         # X_tfidf = tfidf.fit_transform(X).toarray()
    #         y = np.array(lv)
    #         scores = []
    #         for metric in ["precision", "recall", "f1", "accuracy"]:
    #             scores.append(cross_validation.cross_val_score(clf, X, y, cv=10, scoring=metric).mean())
    #         print("% 20s\tP=%0.2f\tR=%0.2f\tF1=%0.2f\t\tAcc=%0.2f"%(probandId, scores[0], scores[1], scores[2], scores[3]))
    #         prec.append(scores[0])
    #         rec.append(scores[1])
    #         f1.append(scores[2])
    #         acc.append(scores[3])
    #
    # print "% 20s\tP=%0.2f\tR=%0.2f\tF1=%0.2f\t\tAcc=%0.2f\n" % ("Durchschnitt:", np.mean(prec),np.mean(rec),np.mean(f1),np.mean(acc))
    #
    # return (prec,rec,f1,acc)