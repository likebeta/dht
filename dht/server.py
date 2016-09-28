#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import hyperloglog
from util.log import Logger
from dht.kademlia.server import DHTServer
from dht.kademlia.const import NODE_COUNT
from twisted.internet import reactor


class simDHT(object):
    def __init__(self):
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
            Logger.info("%s %s %s" % (ip, port, hex_hash))
            from downloader import Downloader
            result = Downloader.download_metadata(info_hash, (ip, port), peer_id)
            if result:
                with open("torrent/" + result[0], 'w') as fp:
                    fp.write(result[1])


if __name__ == '__main__':
    import os
    if not os.path.exists('torrent'):
        os.makedirs('torrent')
    Logger.show_task_id(False)
    Logger.open_std_log()
    for i in range(NODE_COUNT):
        reactor.listenUDP(6882 + i, DHTServer(simDHT()))
        Logger.info('listen on udp port', 6882 + i)
    reactor.run()
