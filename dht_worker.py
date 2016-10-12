#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import json
# import bencode
import setting
# import hyperloglog
from util.log import Logger
from dht.kademlia.server import DHTServer
from dht.kademlia.const import NODE_COUNT
from twisted.internet import reactor
from twisted.internet import defer
from dht.protocol import TcpClientFactory
from dht.parser import Parser
from collections import defaultdict


class DHTWorker(object):
    def __init__(self, save_path):
        # self.hp = hyperloglog.HyperLogLog(0.01)
        # self.hp_len = 0
        self.bt_hit = defaultdict(int)
        self.dl_ing = set()
        self.dl_ed = set()
        self.save_path = save_path

    def on_metadata(self, info_hash, ip, port, peer_id):
        """
        种子下载, 可以通过迅雷种子, 种子协议, libtorrent下载
        """
        # self.hp.add(info_hash)
        # hp_len = self.hp.card()
        # if self.hp_len != hp_len:
        #     self.hp_len = hp_len
        self.bt_hit[info_hash] += 1
        need_download = False
        hex_hash = info_hash.encode('hex')
        if info_hash not in self.dl_ed:
            if info_hash not in self.dl_ing:
                if os.path.exists('%s/%s' % (self.save_path, hex_hash)):
                    self.dl_ed.add(info_hash)
                else:
                    self.dl_ing.add(info_hash)
                    need_download = True

        if need_download:
            Logger.info(hex_hash, ip, port)
            d = defer.Deferred()
            d.addCallback(self.on_success_download, info_hash, hex_hash)
            d.addErrback(self.on_failed_download, info_hash, hex_hash)
            factory = TcpClientFactory(d, info_hash, peer_id)
            reactor.connectTCP(ip, port, factory)

        if self.bt_hit[info_hash] > 3 and info_hash in self.dl_ed:
            self.update_hit(info_hash, hex_hash)

    def update_hit(self, info_hash, hex_hash):
        try:
            with open('%s/%s' % (self.save_path, hex_hash), 'r+') as f:
                data = f.read()
                info = json.loads(data)
                if 'hit' in info:
                    info['hit'] += self.bt_hit[info_hash]
                else:
                    info['hit'] = self.bt_hit[info_hash]
                data = json.dumps(info, separators=(',', ':'))
                f.truncate(0)
                f.seek(0)
                f.write(data)
                self.bt_hit[info_hash] = 0
        except:
            Logger.exception()
            Logger.error('open', hex_hash, 'failed')

    def on_success_download(self, metadata, info_hash, hex_hash):
        Logger.info(hex_hash, 'success', metadata['name'])
        self.dl_ing.discard(info_hash)
        info, _ = Parser.parse_torrent(metadata)
        if info:
            info['hit'], self.bt_hit[info_hash] = self.bt_hit[info_hash], 0
            data_json = json.dumps(info, separators=(',', ':'))
            with open('%s/%s' % (self.save_path, hex_hash), 'w') as fp:
                fp.write(data_json)
            self.dl_ed.add(info_hash)

    def on_failed_download(self, error, info_hash, hex_hash):
        self.dl_ing.discard(info_hash)
        Logger.info(hex_hash, 'failed', error.getErrorMessage())


if __name__ == '__main__':
    import os

    if not os.path.exists(setting.dht_metadata_path):
        os.makedirs(setting.dht_metadata_path)
    Logger.show_task_id(False)
    Logger.open_std_log()
    worker = DHTWorker(setting.dht_metadata_path)
    for i in range(NODE_COUNT):
        reactor.listenUDP(6882 + i, DHTServer(worker))
        Logger.info('listen on udp port', 6882 + i)
    reactor.run()
