# -*- coding: utf-8 -*-

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.externals import joblib
from sklearn import metrics
from nltk.corpus import stopwords
import pymorphy2
import pandas as pd
import numpy as np


class Model:

    def __init__(self, load_model_from_file=True):
        self.themes = self.handle_themes_data()
        self.train_data = pd.read_csv('train.csv')
        self.X = self.train_data['Speech']
        self.y = self.train_data['ThemeLabel']
        self.n = 7000
        self.clf = None
        self.delta = 0.3
        self.morph = pymorphy2.MorphAnalyzer()
        if load_model_from_file:
            self.load()

    def handle_themes_data(self):
        data = pd.read_csv('themes.csv', names=['index', 'label'])
        return list(data['label'])

    def get_response(self, message):
        message = [self.normalize(message)]
        num_labels = zip(list(range(len(self.themes))), self.evaluate(message)[0])
        num_labels = [(x, self.reg_coef(x, y)) for x, y in num_labels]
        num_labels = list(filter(lambda x: x[1] >= self.delta, num_labels))
        num_labels = sorted(num_labels, key=lambda x: x[1], reverse=True)
        num_labels = num_labels[:min(4, len(num_labels))]
        num_labels = [(x, self.themes[x]) for x, y in num_labels]
        return num_labels

    def reg_coef(self, n, k):
        if n == 0:
            return k * 0.9
        if n == 10:
            return k * 0.88
        if n == 9:
            return k * 0.925
        if n == 19:
            return k * 1.15
        if n == 20:
            return k * 0.925
        if n == 28:
            return k * 1.12
        if n == 29:
            return k * 1.07
        if n == 31:
            return k * 0.88
        if n == 32:
            return k * 1.1
        return k

    def evaluate(self, X):
        X = [self.normalize(txt) for txt in X]
        predicted = self.clf.predict_proba(X)
        predicted = [[self.reg_coef(i, p[i]) for i in range(len(p))] for p in predicted]
        return predicted

    def normalize(self, text):
        punct = ';:?/"\'+=-)(*&^%$#@!1234567890[]{}<>'
        stop = set(stopwords.words('russian'))
        tmp_list = []
        for word in text.split(' '):
            for c in punct:
                word.replace(c, '')
            word = self.morph.parse(word)[0].normal_form
            if word not in stop:
                tmp_list.append(word)
        return ' '.join(tmp_list)

    def train(self):
        X = [self.normalize(txt) for txt in self.train_data['Speech']]
        y = self.train_data['ThemeLabel']
        text_clf = Pipeline([
            ('vect', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', SGDClassifier())])
        params = {
            'vect__ngram_range': [(1, 1), (1, 2)],
            'tfidf__use_idf': (True, False),
            'tfidf__norm': ('l1', 'l2'),
            'tfidf__use_idf': (True, False),
            'clf__loss': ['log', 'modified_huber'],
            'clf__n_iter': [10],
            'clf__alpha': (1e-2, 1e-3, 1e-4),
            'clf__penalty': ('none', 'l1', 'l2', 'elasticnet'),
        }
        self.clf = GridSearchCV(text_clf, params, n_jobs=-1, cv=4)
        self.clf = self.clf.fit(X, y)

    def eval_csv(self, name):
        data = pd.read_csv(name)
        df = pd.DataFrame({
            'Index': data['Index'],
            'ThemeLabel': [x.index(max(x)) for x in self.evaluate(data['Speech'])]
        })
        df.to_csv('out_' + name, sep=',', index=False, encoding='utf-8')

    def load(self):
        self.clf = joblib.load('model.pkl')

    def save(self):
        joblib.dump(self.clf, 'model.pkl')
