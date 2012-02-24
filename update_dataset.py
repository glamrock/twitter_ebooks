#!/usr/bin/env python

import yaml
import os
import sys
import twitter
import time
import codecs
from traceback import print_exc

if __name__ == '__main__':
    topdir = os.path.dirname(os.path.realpath(__file__))
    settings = yaml.load(open(os.path.join(topdir, 'settings.yml')))
    api = twitter.Api(**settings['auth'])

    try: since_id = open(os.path.join(topdir, '.last_tweet_id'), 'r').read()
    except IOError: since_id = None

    page = 1
    statuses = []
    while True:
        try:
            new = api.GetUserTimeline(settings['target_user'], since_id=since_id, count=200,
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
        sys.exit()

    texts = [s.text for s in statuses]

    datafile_path = os.path.join(topdir, settings['target_user'].replace('@', '') + '.tweets')

    try:
        datafile = codecs.open(datafile_path, encoding='utf-8', mode='r')
		texts.append(datafile.read())
    except IOError:
	  pass

	datafile = codecs.open(datafile_path, encoding='utf-8', mode='w')
	datafile.write("\n".join(texts))
    ltf = open(os.path.join(topdir, '.last_tweet_id'), 'w')
    ltf.write(str(statuses[0].id))

