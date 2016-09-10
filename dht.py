#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

from kademlia.server import DHTServer
from kademlia.const import NODE_COUNT
from twisted.application import service
from twisted.application import internet


class simDHT(object):
    def __init__(self, f):
        self.f = f

    def on_metadata(self, ip, port, info_hash):
        """
        种子下载, 可以通过迅雷种子, 种子协议, libtorrent下载
        """
        self.f.write("%s %s %s\n" % (ip, port, info_hash.encode("hex")))
        self.f.flush()


application = service.Application("fastbot")
f = open("infohash.log", "a")
for i in range(NODE_COUNT):
    internet.UDPServer(6882 + i, DHTServer(simDHT(f))).setServiceParent(application)
