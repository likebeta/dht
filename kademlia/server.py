#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import const
import utils
import traceback
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
                "r": {
                    "id": self.nid
                }
            }
            self.nodes.append((nid, address))
            self.send_response(msg, address)
        except KeyError:
            pass

    def on_find_node(self, res, address):
        """
        回应find_node请求
        """
        try:
            target = res["a"]["target"]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {
                    "id": self.get_neighbor(target, self.nid),
                    "nodes": ''
                }
            }
            # nid = res["a"]["id"]
            # self.nodes.append((nid, address))
            self.send_response(msg, address)
        except KeyError:
            pass

    def on_get_peers(self, res, address):
        """
        回应get_peers请求, 差不多跟on_find_node一样, 只回复nodes. 懒得维护peer信息
        """
        try:
            info_hash = res["a"]["info_hash"]
            nid = res["a"]["id"]
            token = utils.sha1_encode(info_hash + nid)[:const.TOKEN_LENGTH]
            msg = {
                "t": res["t"],
                "y": "r",
                "r": {
                    "id": self.get_neighbor(info_hash, self.nid),
                    "nodes": '',
                    "token": token
                }
            }
            # self.nodes.append((nid, address))
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
        except KeyError:
            pass
        finally:
            self.success(res, address)
