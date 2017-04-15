# -*- coding: utf-8 -*-

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.externals import joblib
from nltk.corpus import stopwords
import pandas as pd
import numpy as np


class Model():

    def __init__(self, load_model_from_file=True):
        self.themes = self.handle_themes_data()
        self.train_data = pd.read_csv('train.csv')
        self.text_clf = None
        if load_model_from_file:
            self.load()

    def handle_themes_data(self):
        data = pd.read_csv('themes.csv', names=['index', 'label'])
        return list(data['label'])

    def get_response(self, message):
        message = [message]
        num_labels = self.text_clf.predict(message)
        labels = [self.themes[x] for x in num_labels]
        response = {
            'pos_themes': labels,
            'type': 'choose_theme' if len(labels) > 1 else 'get_confirmation'
        }
        return response

    def evaluate(self, X, y):
        predicted = self.text_clf.predict(X)
        return np.mean(predicted == y)

    def normalize(self, data):
        stop = set(stopwords.words('russian'))
        for text in data:
            for word in stop:
                text = text.replace(word, '').lower()
        return data

    def train(self):
        X = self.normalize(self.train_data['Speech'])
        y = self.train_data['ThemeLabel']
        self.text_clf = Pipeline([
            ('vect', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', SGDClassifier(loss='hinge', penalty='l2', alpha=1e-3, n_iter=5, random_state=42))])
        self.text_clf = self.text_clf.fit(X, y)

    def load(self):
        self.text_clf = joblib.load('model.pkl')

    def save(self):
        joblib.dump(self.text_clf, 'model.pkl')


if __name__ == '__main__':
    model = Model(load_model_from_file=True)
    model.train()
    print('Accuracy:', model.evaluate(model.train_data['Speech'], model.train_data['ThemeLabel']))
    print(model.get_response(model.train_data['Speech'][0]))
    model.save()
