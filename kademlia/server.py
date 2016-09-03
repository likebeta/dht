#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import const
import utils
from table import KNode
from client import DHTClient


class DHTServer(DHTClient):
    """
    服务端必须实现回应ping, find_node, get_peers announce_peer请求
    """

    def __init__(self, handler):
        DHTClient.__init__(self)
        self.handler = handler

    def startProtocol(self):
        self.join_network()

    def on_ping(self, res, address):
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
            ip, port = address
            self.table.append(KNode(nid, ip, port))
            self.send_response(msg, address)
        except KeyError:
            pass

    def on_find_node(self, res, address):
        """
        回应find_node请求
        """
        try:
            target = res["a"]["target"]
            close_nodes = self.table.find_close_nodes(target, 16)
            if not close_nodes:
                return

            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": utils.encode_nodes(close_nodes)}
            }
            nid = res["a"]["id"]
            ip, port = address
            self.table.append(KNode(nid, ip, port))
            self.send_response(msg, address)
        except KeyError:
            pass

    def on_get_peers(self, res, address):
        """
        回应get_peers请求, 差不多跟on_find_node一样, 只回复nodes. 懒得维护peer信息
        """
        try:
            info_hash = res["a"]["info_hash"]
            close_nodes = self.table.find_close_nodes(info_hash, 16)
            if not close_nodes:
                return

            nid = res["a"]["id"]
            token = utils.sha1_encode(info_hash + nid)[:const.TOKEN_LENGTH]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid, "nodes": utils.encode_nodes(close_nodes), "token": token}
            }
            ip, port = address
            self.table.append(KNode(nid, ip, port))
            self.send_response(msg, address)
        except KeyError:
            pass

    def on_announce_peer(self, res, address):
        """
        回应announce_peer请求
        """
        try:
            info_hash = res["a"]["info_hash"]
            token = res["a"]["token"]
            nid = res["a"]["id"]
            _token = utils.sha1_encode(info_hash + nid)[:const.TOKEN_LENGTH]
            if _token == token:
                # 验证token成功, 开始下载种子
                ip, port = address
                port = res["a"]["port"]
                self.handler.on_metadata(ip, port, info_hash)
            self.table.touch_bucket(nid)
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {"id": self.table.nid}
            }
            self.send_response(msg, address)
        except KeyError:
            pass
