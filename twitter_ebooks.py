#!/usr/bin/env python

import nltk
from nltk import LidstoneProbDist, NgramModel
import re
import random
import os
import yaml
import twitter

TOPDIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS = yaml.load(open(os.path.join(TOPDIR, 'settings.yml')))

class Generator:
    def __init__(self, target_user):
        self.target_user = target_user.replace('@', '')
        dataset = open(os.path.join(TOPDIR, self.target_user + '.tweets')).read()
        tweets = dataset.split("\n")
        words = []
        for tweet in tweets:
            if "@" in tweet or tweet.startswith("RT"):
                continue
            words += [word for word in tweet.split() if word[0] != "@"]
        self.model = nltk.Text(words)

    def raw_words(self, length=100):
        if not hasattr(self, '_trigram_model'):
            estimator = lambda fdist, bins: LidstoneProbDist(fdist, 0.2)
            self._trigram_model = NgramModel(2, self.model, estimator)
        return self._trigram_model.generate(length, (".",))[1:]

    def smart_trim(self, genwords):
        new_words = genwords[:]
        # Proper sentence markings
        stoppers = r'[.?!]'
        for i, word in enumerate(new_words):
            if (i == 0 or re.search(stoppers, new_words[i-1][-1])) and not word.startswith("http"):
                new_words[i] = word.capitalize()

        # Cleverly trim to tweet size
        while True:
            short_enough = (sum([len(word)+1 for word in new_words]) < 140)
            if len(new_words) <= 1 or (short_enough and re.search(stoppers, new_words[-1])):
                break
            new_words.pop()

        return new_words

    def tweetworthy(self, care_about_punctuation=True):
        genwords = self.raw_words()

        if care_about_punctuation:
            genwords = self.smart_trim(genwords)

        while len(genwords) > 1 and sum([len(word)+1 for word in genwords]) > 140:
            genwords.pop()
            if care_about_punctuation:
                genwords[-1] += random.choice(['.', '!', '?'])

        product = " ".join(genwords)
        if len(product) > 140: product = product[0:140]

        # Remove mismatched enclosures
        for pair in [['(', ')']]:
            if product.count(pair[0]) != product.count(pair[1]):
                product = product.replace(pair[0], '').replace(pair[1], '')

        for enc in ['"', '*']:
            if product.count(enc) % 2 != 0:
                product = product.replace(enc, '')

        return product


if __name__ == '__main__':
    gen = Generator(SETTINGS['target_user'])
    tweet = gen.tweetworthy()
    print tweet

    api = twitter.Api(**SETTINGS['auth'])
    api.PostUpdate(tweet)
