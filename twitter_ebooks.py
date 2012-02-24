#!/usr/bin/env python

import nltk
from nltk import LidstoneProbDist, NgramModel
import re
import random
import os
import yaml
import twitter
import sys

TOPDIR = os.path.dirname(os.path.realpath(__file__))
SETTINGS = yaml.load(open(os.path.join(TOPDIR, 'settings.yml')))

class Generator:
    def __init__(self, target_user, settings):
        self.target_user = target_user.replace('@', '')
        self.settings = settings
        dataset = open(os.path.join(TOPDIR, 'users', self.target_user, 'tweets')).read()
        tweets = dataset.split("\n")
        words = []
        for tweet in tweets:
            if "@" in tweet or tweet.startswith("RT"):
                continue
            words += [word for word in tweet.split() if word[0] != "@" and not "http://" in word]
        self.words = words
        self.model = nltk.Text(words)

    def raw_words(self, length=100):
        if not hasattr(self, '_trigram_model'):
            estimator = lambda fdist, bins: LidstoneProbDist(fdist, 0.2)
            self._trigram_model = NgramModel(2, self.model, estimator)
        return self._trigram_model.generate(length, [random.choice(self.words)])[1:]

    def smart_trim(self, genwords):
        new_words = genwords[:]

        # Cleverly trim to tweet size
        stoppers = r'[.?!]'
        while True:
            short_enough = (sum([len(word)+1 for word in new_words]) < 140)
            if short_enough and re.search(stoppers, new_words[-1]):
                break
            if len(new_words) <= 1:
                new_words = genwords[:]
                break
            new_words.pop()

        # Proper sentence markings
        for i, word in enumerate(new_words):
            if i == 0  or re.search(stoppers, new_words[i-1][-1]):
                new_words[i] = word.capitalize()



        return new_words

    def tweetworthy(self):
        capitalize = self.settings['capitalize'] if self.settings.has_key('capitalize') else False
        genwords = self.raw_words()

        if capitalize:
            genwords = self.smart_trim(genwords)

        while len(genwords) > 1 and sum([len(word)+1 for word in genwords]) > 140:
            genwords.pop()
            if capitalize:
                genwords[-1] += random.choice(['.', '!', '?'])

        product = " ".join(genwords)
        if len(product) > 140: product = product[0:140]

        # Remove mismatched enclosures
        for pair in [['(', ')'], ['{', '}'], ['[', ']']]:
            if product.count(pair[0]) != product.count(pair[1]):
                product = product.replace(pair[0], '').replace(pair[1], '')

        for enc in ['"', '*']:
            if product.count(enc) % 2 != 0:
                product = product.replace(enc, '')

        return product


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s @parody_account" % sys.argv[0]
        sys.exit()

    username = sys.argv[1]
    target = SETTINGS[username]['target'].replace('@','')

    if not os.path.exists(os.path.join(TOPDIR, 'users', target, 'tweets')):
        from update_dataset import update_dataset
        update_dataset(target)

    gen = Generator(target, SETTINGS[username])
    tweet = gen.tweetworthy()
    print tweet

    api = twitter.Api(**SETTINGS[username]['auth'])
    api.PostUpdate(tweet)
