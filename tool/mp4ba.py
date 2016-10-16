#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-15

from twisted.internet import reactor
from twisted.web import client
from twisted.internet import defer
from pyquery import PyQuery
from util.tool import Time
from util.log import Logger


class Mp4Ba(object):
    URL = 'http://www.mp4ba.com'

    def __init__(self, start=None, worker=3):
        self.start = start
        self.worker = worker

    @defer.inlineCallbacks
    def run(self):
        Logger.debug('start download index page:', self.URL)
        html = yield client.getPage(self.URL)
        Logger.debug('start parsing index page:', self.URL)
        

    def parse_index_page(self):
        pass

    def parse_list_page(self, page):
        pass

    def parse_detail_page(self, info_hash):
        pass


if __name__ == "__main__":
    Logger.show_task_id(False)
    Logger.open_std_log()
    app = Mp4Ba()
    d = app.run()
    d.addErrback(lambda _: Logger.exception())
    d.addBoth(lambda _: reactor.stop())
    # reactor.callWhenRunning(main)
    reactor.run()
