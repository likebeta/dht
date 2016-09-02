#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02


from twisted.application import service, internet

from kademlia.table import KTable
from kademlia.server import DHTServer
from kademlia.utils import new_node_id
from kademlia.const import NODE_COUNT


class simDHT(object):
    def __init__(self, f):
        self.table = KTable(new_node_id())
        self.f = f

    def downloadTorrent(self, ip, port, infohash):
        """
        种子下载, 可以通过迅雷种子, 种子协议, libtorrent下载
        """
        self.f.write("%s %s %s\n" % (ip, port, infohash.encode("hex")))
        self.f.flush()


application = service.Application("fastbot")
f = open("infohash.log", "w")
for i in range(NODE_COUNT):
    internet.UDPServer(0, DHTServer(simDHT(f))).setServiceParent(application)
