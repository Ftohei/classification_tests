from nltk import word_tokenize
from nltk import FreqDist

from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction import DictVectorizer

sentence = 'Hi, I am Fabian and i am trying out tfidf with nltk and sklearn'

fdist = FreqDist(word.lower() for word in word_tokenize(sentence))


count_dict = {}
for word in (word.lower() for word in word_tokenize(sentence)):
    count_dict[word] = fdist[word]

print sentence
print count_dict

vec = DictVectorizer()

vec_dict = vec.fit_transform([count_dict,count_dict]).toarray()

print vec_dict

tfidf = TfidfTransformer()

print tfidf.fit_transform(vec_dict).to



# print tfidf.fit_transform(sentence)
#
# print sentence
