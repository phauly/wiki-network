#!/usr/bin/env python

##########################################################################
#                                                                        #
#  This program is free software; you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation; version 2 of the License.               #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
#                                                                        #
##########################################################################

## LXML
from lxml import etree

from datetime import datetime
import sys
import re

## PROJECT LIBS
import mwlib
from lib import SevenZipFileExt
from mwlib import PageProcessor

def isNearAnniversary(creation, revision, range_):
    """
    >>> isNearAnniversary(datetime(2001, 9, 11), datetime(2005, 9, 19), 10)
    True
    >>> isNearAnniversary(datetime(2001, 1, 1), datetime(2005, 12, 30), 10)
    True
    >>> isNearAnniversary(datetime(2001, 12, 31), datetime(2005, 1, 1), 10)
    True
    """
    isinstance(revision, datetime) ##WING IDE
    isinstance(creation, datetime) ##WING IDE
    anniversary = datetime(revision.year, creation.month, creation.day)
    delta = (revision - anniversary).days
    if abs(delta) <= range_:
        return True
    else:
        if delta > 0:
            anniversary = datetime(revision.year + 1, creation.month,
                                   creation.day)
            delta = (revision - anniversary).days
            if abs(delta) <= range_:
                return True
        else:
            anniversary = datetime(revision.year - 1, creation.month,
                                   creation.day)
            delta = (revision - anniversary).days
            if abs(delta) <= range_:
                return True
        return False

class HistoryEventsPageProcessor(PageProcessor):
    ## count only revisions 'days' before or after the anniversary
    days = 10
    ## counter for desired pages
    ## total revisions vs revisions near the anniversary
    counter_desired = None
    counter_normal = {
        'talk': {'total': 0, 'anniversary': 0},
        'normal': {'total': 0, 'anniversary': 0}
    }
    counter_pages = 0

    def setDesired(self, l):
        self.counter_desired = {}
        for page in l:
            self.counter_desired[page] = {
                'talk': {
                    'total': 0,
                    'anniversary': 0
                },
                'normal': {
                    'total': 0,
                    'anniversary': 0
                }
            }


    def isDesired(self, title):
        try:
            self.counter_desired[title]
        except KeyError:
            return False
        else:
            return True


    def process(self, elem):
        tag = self.tag
        creation = None
        for el in elem:
            if el.tag == tag['title']:
                title = el.text
                break
        a_title = title.split(':')
        if len(a_title) == 1:
            type_ = 'normal'
            title = a_title[0]
        else:
            if a_title[0] == 'Talk':
                title = a_title[1]
                type_ = 'talk'
            else:
                return
        self.counter_pages += 1

        if self.isDesired(title):
            desired = True
        else:
            desired = False

        for child in elem.getiterator(tag['revision']): ##or elem.findall(...)
            for el in child:
                if el.tag == tag['timestamp']:
                    timestamp = el.text
                    break
            #revision_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")
            #m = re.match('(\d{4})-(\d{2})-(\d{2}).*', timestamp)
            #revision_time = datetime(m.group(0), m.group(1))
            year = int(timestamp[:4])
            month = int(timestamp[5:7])
            day = int(timestamp[8:10])
            revision_time = datetime(year, month, day)

            if creation is None:
                if month == 2 and day == 29:
                    creation = datetime(year, 2, 28)
                else:
                    creation = revision_time
                continue

            if (revision_time - creation).days < 180:
                continue

            isNear = isNearAnniversary(creation, revision_time, self.days)
            if desired:
                page_counter = self.counter_desired[title][type_]
            else:
                page_counter = self.counter_normal[type_]
            if isNear:
                page_counter['anniversary'] += 1
            page_counter['total'] += 1

            self.count += 1
            if not self.count % 5000:
                print 'PAGES:', self.counter_pages, 'REVS:', self.count
                print 'DESIRED'
                for page, counter in self.counter_desired.iteritems():
                    print page
                    print counter
                print 'NORMAL'
                print self.counter_normal
            #del child


def main():
    import optparse

    p = optparse.OptionParser(usage="usage: %prog [options] file")
    _, files = p.parse_args()

    if not files:
        p.error("Give me a file, please ;-)")
    xml = files[0]
    desired_pages_fn = files[1]
    with open(desired_pages_fn) as f:
        lines = f.readlines()
    desired_pages = [l for l in [l.strip() for l in lines] if l and not l[0] == '#']

    lang, date, type_ = mwlib.explode_dump_filename(xml)

    src = SevenZipFileExt(xml, 51)

    tag = mwlib.getTags(src)

    src.close()
    src = SevenZipFileExt(xml)
    processor = HistoryEventsPageProcessor(tag=tag, lang=lang)
    processor.setDesired(desired_pages)

    print "BEGIN PARSING"
    mwlib.fast_iter(etree.iterparse(src, tag=tag['page'], strip_cdata=False),
                    processor.process)

    print 'DESIRED'
    print processor.counter_desired
    print 'NORMAL'
    print processor.counter_normal


if __name__ == "__main__":
    #import cProfile as profile
    #profile.run('main()', 'mainprof')
    main()
