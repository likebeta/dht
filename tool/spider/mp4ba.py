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

    def __init__(self, start=None, worker=2):
        self.start = start
        self.worker = worker

    def fetch_pages(self, *urls):
        if len(urls) == 1:
            Logger.debug('start fetch page:', urls[0])
            return client.getPage(urls[0])
        dl = []
        for url in urls:
            Logger.debug('start fetch page:', url)
            dl.append(client.getPage(url))
        if dl:
            return defer.DeferredList(dl, consumeErrors=True)

    @defer.inlineCallbacks
    def run(self):
        html = yield self.fetch_pages(self.URL)
        Logger.debug('start parse page:', self.URL)
        pq = PyQuery(html)
        total_page = int(pq('.pages .pager-last').text())
        Logger.debug('total page:', total_page)
        pages = range(1, total_page + 1)
        groups = [pages[i:i + self.worker] for i in xrange(0, len(pages), self.worker)]
        for group in groups:
            urls = ['http://www.mp4ba.com/4545index.php?page=' + str(i) for i in group]
            htmls = yield self.fetch_pages(*urls)
            for success, html in htmls:
                if success:
                    self.parse_index_page(html)
                else:
                    Logger.debug('')

    def parse_index_page(self, html):
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
