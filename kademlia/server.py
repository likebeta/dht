#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import const
import hashlib
from client import DHTClient
from utils import encode_nodes
from ktable import KNode


class DHTServer(DHTClient):
    """
    DHT服务器端

    服务端必须实现回应ping, find_node, get_peers announce_peer请求
    """

    def __init__(self, fastbot):
        self.fastbot = fastbot
        self.table = fastbot.table
        DHTClient.__init__(self)

    def startProtocol(self):
        self.joinNetwork()

    def pingReceived(self, res, address):
        """
        回应ping请求
        """
        try:
            nid = res["a"]["id"]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid}
            }
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.sendResponse(msg, address)
        except KeyError:
            pass

    def findNodeReceived(self, res, address):
        """
        回应find_node请求
        """
        try:
            target = res["a"]["target"]
            closeNodes = self.table.findCloseNodes(target, 16)
            if not closeNodes:
                return

            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": encode_nodes(closeNodes)}
            }
            nid = res["a"]["id"]
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.sendResponse(msg, address)
        except KeyError:
            pass

    def getPeersReceived(self, res, address):
        """
        回应get_peers请求, 差不多跟findNodeReceived一样, 只回复nodes. 懒得维护peer信息
        """
        try:
            infohash = res["a"]["info_hash"]
            closeNodes = self.table.findCloseNodes(infohash, 16)
            if not closeNodes:
                return

            nid = res["a"]["id"]
            h = hashlib.sha1()
            h.update(infohash + nid)
            token = h.hexdigest()[:const.TOKEN_LENGTH]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": encode_nodes(closeNodes), "token": token}
            }
            (ip, port) = address
            self.table.append(KNode(nid, ip, port))
            self.sendResponse(msg, address)
        except KeyError:
            pass

    def announcePeerReceived(self, res, address):
        """
        回应announce_peer请求
        """
        try:
            infohash = res["a"]["info_hash"]
            token = res["a"]["token"]
            nid = res["a"]["id"]
            h = hashlib.sha1()
            h.update(infohash + nid)
            if h.hexdigest()[:const.TOKEN_LENGTH] == token:
                # 验证token成功, 开始下载种子
                (ip, port) = address
                port = res["a"]["port"]
                self.fastbot.downloadTorrent(ip, port, infohash)
            self.table.touchBucket(nid)
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid}
            }
            self.sendResponse(msg, address)
        except KeyError:
            pass
