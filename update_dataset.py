#!/usr/bin/env python

import yaml
import os
import sys
import twitter
import time
import codecs
from traceback import print_exc

def update_dataset(username):
    """Fetches as many tweets as possible for the given user since the last one we received."""
    username = username.replace('@', '')
    print "Retrieving tweets from @%s" % username
    topdir = os.path.dirname(os.path.realpath(__file__))
    settings = yaml.load(open(os.path.join(topdir, 'settings.yml')))

    auth = None
    for sett in settings.itervalues():
        if sett['target'].replace('@','') == username:
            auth = sett['auth']


    api = twitter.Api(**auth)

    userdir = os.path.join(topdir, 'users', username)
    if not os.path.exists(userdir):
        os.makedirs(userdir)

    lti_path = os.path.join(userdir, 'last_tweet_id')
    try: since_id = open(lti_path, 'r').read()
    except IOError: since_id = None

    page = 1
    statuses = []
    while True:
        try:
            new = api.GetUserTimeline(username, since_id=since_id, count=200,
                                      include_rts=False, page=page)
            if len(new) == 0: break
            statuses += new
            print "Received %d tweets..." % len(statuses)
            page += 1
        except twitter.TwitterError:
            print_exc()
            print "Retrying in 5 seconds..."
            time.sleep(5)

    if len(statuses) == 0:
        print "No new tweets."
        return

    texts = [s.text.replace("\n", " ") for s in statuses]

    datafile_path = os.path.join(userdir, 'tweets')

    try:
        datafile = codecs.open(datafile_path, encoding='utf-8', mode='r')
        texts.append(datafile.read())
    except IOError:
      pass

    datafile = codecs.open(datafile_path, encoding='utf-8', mode='w')
    datafile.write("\n".join(texts))
    ltf = open(os.path.join(userdir, 'last_tweet_id'), 'w')
    ltf.write(str(statuses[0].id))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Usage: %s @target_account" % sys.argv[0]
        sys.exit()
    update_dataset(sys.argv[1])
