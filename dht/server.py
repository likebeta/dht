#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import json
# import bencode
import hyperloglog
from util.log import Logger
from dht.kademlia.server import DHTServer
from dht.kademlia.const import NODE_COUNT
from twisted.internet import reactor
from twisted.internet import defer
from dht.protocol import TcpClientFactory
from dht.parser import Parser


class simDHT(object):
    def __init__(self):
        self.hp = hyperloglog.HyperLogLog(0.01)
        self.hp_len = 0
        self.dl_set = set()

    def on_metadata(self, info_hash, ip, port, peer_id):
        """
        种子下载, 可以通过迅雷种子, 种子协议, libtorrent下载
        """
        # self.hp.add(info_hash)
        # hp_len = self.hp.card()
        # if self.hp_len != hp_len:
        #     self.hp_len = hp_len
        if info_hash not in self.dl_set:
            self.dl_set.add(info_hash)
            hex_hash = info_hash.encode('hex')
            # if not os.path.exists('metadata/%s' % hex_hash):
            Logger.info(hex_hash, ip, port)
            d = defer.Deferred()
            d.addCallback(self.on_success_download, hex_hash)
            d.addErrback(self.on_failed_download, hex_hash)
            factory = TcpClientFactory(d, info_hash, peer_id)
            reactor.connectTCP(ip, port, factory)

    def on_success_download(self, metadata, hex_hash):
        Logger.info(hex_hash, 'success', metadata['name'])
        info = Parser.parse_torrent(metadata)
        if info:
            data_json = json.dumps(info, separators=(',', ':'))
            with open('metadata/%s' % hex_hash, 'w') as fp:
                fp.write(data_json)

    def on_failed_download(self, error, hex_hash):
        self.dl_set.discard(hex_hash)
        Logger.info(hex_hash, 'failed', error.getErrorMessage())


if __name__ == '__main__':
    import os

    if not os.path.exists('metadata'):
        os.makedirs('metadata')
    Logger.show_task_id(False)
    Logger.open_std_log()
    for i in range(NODE_COUNT):
        reactor.listenUDP(6882 + i, DHTServer(simDHT()))
        Logger.info('listen on udp port', 6882 + i)
    reactor.run()
