# -*- coding: utf-8 -*-

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.svm import SVC
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
        self.clf = None
        self.morph = pymorphy2.MorphAnalyzer()
        if load_model_from_file:
            self.load()

    def handle_themes_data(self):
        data = pd.read_csv('themes.csv', names=['index', 'label'])
        return list(data['label'])

    def get_response(self, message):
        message = [self.normalize(message)]
        num_labels = self.clf.predict(message)
        labels = [self.themes[x] for x in num_labels]
        response = {
            'pos_themes': labels,
            'type': 'choose_theme' if len(labels) > 1 else 'get_confirmation'
        }
        return response

    def evaluate(self, X, y):
        X = [self.normalize(txt) for txt in X]
        predicted = self.clf.predict(X)
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
        X = [self.normalize(txt) for txt in self.X]
        y = self.y
        text_clf = Pipeline([
            ('vect', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', SVC())])
        parameters = {
            'vect__max_features': (None, 1000, 5000),
            'vect__ngram_range': ((1, 1), (1, 2)),
            'tfidf__use_idf': (True, False),
            'tfidf__norm': ('l1', 'l2'),
            'clf__C': [1, 10, 0.1, 0.5],
            'clf__kernel': ['rbf', 'poly', 'linear', 'sigmoid'],
            'clf__degree': [1, 2, 3],
            'clf__gamma': ['auto', 1e-3, 1e-4]
        }
        self.clf = GridSearchCV(text_clf, parameters, n_jobs=-1, cv=4)
        self.clf = self.clf.fit(X, y)

    def load(self):
        self.clf = joblib.load('model.pkl')

    def save(self):
        joblib.dump(self.clf, 'model.pkl')


if __name__ == '__main__':
    model = Model(load_model_from_file=False)
    model.train()
    X = model.train_data['Speech']
    y = model.train_data['ThemeLabel']
    eval = model.evaluate(X, y)
    metric = metrics.classification_report(y, eval, target_names=model.themes)
    print(metric)
    model.save()
