#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import time
import const
import utils
import collections
from rpc import KRPC
from util.log import Logger
from twisted.internet import reactor
from twisted.application import internet


def timer(step, callback, *args):
    """定时器"""
    s = internet.TimerService(step, callback, *args)
    s.startService()
    return s


class DHTClient(KRPC):
    def __init__(self):
        KRPC.__init__(self)
        self.nid = utils.random_node_id()
        self.nodes = collections.deque(maxlen=10000)
        self.last_find_ts = time.time()
        timer(const.FIND_TIMEOUT, self.rejoin_network)
        timer(const.FIND_NODE_INTERVAL, self.find_node)

    def find_node(self, *nodes):
        """
        DHT爬虫的客户端至少要实现find_node.
        此方法最主要的功能就是不停地让更多人认识自己.
        爬虫只需认识(160^2) * K 个节点即可
        """
        if nodes:
            for node in nodes:
                self.send_find_node(node)
        else:
            if len(self.nodes):
                node = self.nodes.popleft()
                self.send_find_node(node)

    def send_find_node(self, node):
        nid, address = node
        tid = utils.entropy(const.TID_LENGTH)
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {
                "id": self.get_neighbor(nid, self.nid),
                "target": utils.random_node_id()
            }
        }
        self.send_query(msg, address)

    def on_ack_find_node(self, res):
        """
        处理find_node回应数据
        """
        try:
            nodes = utils.decode_nodes(res["r"]["nodes"])
            for node in nodes:
                nid, _ = node
                if nid == self.nid:
                    continue
                self.nodes.append(node)

            self.last_find_ts = time.time()  # 最后请求时间
        except KeyError:
            pass

    def join_network(self):
        """加入DHT网络"""
        for address in const.BOOTSTRAP_NODES:
            self.resolve(address[0], address[1])
        reactor.callLater(const.KRPC_TIMEOUT, self.join_fail_handle)

    def resolve(self, host, port):
        """解析域名"""

        def callback(ip, port):
            """解析成功后, 开始发送find_node"""
            Logger.debug('callback', ip, host)
            self.find_node((self.nid, (ip, port)))

        def errback(failure, host, port):
            """解析失败, 再继续解析, 直到成功为止"""
            Logger.debug('errback', failure, host, port)
            self.resolve(host, port)

        d = reactor.resolve(host)
        d.addCallback(callback, port)
        d.addErrback(errback, host, port)

    def join_fail_handle(self):
        """加入DHT网络失败, 再继续加入, 直到加入成功为止"""
        if len(self.nodes) == 0:
            self.join_network()

    def rejoin_network(self):
        """
        防止find_node请求停止而打造. 停止后, 再重新加入DHT网络
        """
        if (self.last_find_ts - time.time()) > const.FIND_TIMEOUT:
            self.join_network()

    def success(self, msg, address):
        try:
            tid = msg["t"]
            nid = msg["a"]["id"]
            msg = {
                "t": tid,
                "y": "r",
                "r": {
                    "id": self.get_neighbor(nid, self.nid)
                }
            }
            self.send_response(msg, address)
        except KeyError:
            pass

    def get_neighbor(self, target, nid, end=10):
        return target[:end] + nid[end:]
