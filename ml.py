# -*- coding: utf-8 -*-

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pandas as pd
import numpy as np


def get_response(message):
    pass


def normalize(data):
    pass


def train(X, y):
    text_clf = Pipeline([
        ('vect', CountVectorizer()),
        ('tfidf', TfidfTransformer()),
        ('clf', MultinomialNB())])
    print('Training...')
    text_clf = text_clf.fit(X, y)
    return text_clf


if __name__ == '__main__':
    log = open('log.txt', 'w')
    print('Reading...')
    themes_data = pd.read_csv('themes.csv')
    train_data = pd.read_csv('train.csv')
    print('Setting...')
    text_clf = train(train_data['Speech'], train_data['ThemeLabel'])
    # print(np.mean(predicted == train_data['ThemeLabel']))
    print('Done!')