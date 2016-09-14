#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import hyperloglog
from kademlia.server import DHTServer
from kademlia.const import NODE_COUNT
from twisted.application import service
from twisted.application import internet


class simDHT(object):
    def __init__(self, f):
        self.f = f
        self.hp = hyperloglog.HyperLogLog(0.01)
        self.hp_len = 0

    def on_metadata(self, info_hash, ip, port, peer_id):
        """
        种子下载, 可以通过迅雷种子, 种子协议, libtorrent下载
        """
        hex_hash = info_hash.encode("hex")
        self.hp.add(hex_hash)
        hp_len = self.hp.card()
        if self.hp_len != hp_len:
            self.hp_len = hp_len
            # self.f.write("%s %s %s\n" % (ip, port, hex_hash))
            # self.f.flush()
            print "%s %s %s\n" % (ip, port, hex_hash)
            from downloader import Downloader
            result = Downloader.download_metadata(info_hash, (ip, port), peer_id)
            if result:
                with open(result[0], 'w') as fp:
                    fp.write(result[1])


application = service.Application("fastbot")
f = open("infohash.log", "a")
for i in range(NODE_COUNT):
    internet.UDPServer(6882 + i, DHTServer(simDHT(f))).setServiceParent(application)
