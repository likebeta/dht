#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import time
import const
from rpc import KRPC
from twisted.internet import reactor
from utils import entropy, decode_nodes
from twisted.application import internet
from ktable import KNode


def timer(step, callback, *args):
    """定时器"""
    s = internet.TimerService(step, callback, *args)
    s.startService()
    return s


class DHTClient(KRPC):
    def __init__(self):
        KRPC.__init__(self)
        self.lastFind = time.time()
        timer(const.REFRESH_INTERVAL, self.refreshRoutingTable)
        timer(const.FIND_TIMEOUT, self.rejoinNetwork)

    def findNode(self, address):
        """
        DHT爬虫的客户端至少要实现find_node.
        此方法最主要的功能就是不停地让更多人认识自己.
        爬虫只需认识(160-2) * K 个节点即可
        """
        snid = self.table.nid
        tid = entropy(const.TID_LENGTH)
        msg = {
            "t": tid,
            "y": "q",
            "q": "find_node",
            "a": {"id": snid, "target": snid}
        }
        self.sendQuery(msg, address)

    def findNodeHandle(self, res):
        """
        处理find_node回应数据
        """
        try:
            self.table.touchBucket(res["r"]["id"])

            nodes = decode_nodes(res["r"]["nodes"])
            for node in nodes:
                (nid, ip, port) = node
                if nid == self.table.nid: continue  # 不存自己
                self.table.append(KNode(nid, ip, port))
                self.lastFind = time.time()  # 最后请求时间

                # "等待"NEXT_FIND_NODE_INTERVAL时间后, 进行下一个find_node
                reactor.callLater(const.NEXT_FIND_NODE_INTERVAL, self.findNode, (ip, port))
        except KeyError:
            pass

    def joinNetwork(self):
        """加入DHT网络"""
        for address in const.BOOTSTRAP_NODES:
            self.resolve(address[0], address[1])
        reactor.callLater(const.KRPC_TIMEOUT, self.joinFailHandle)

    def resolve(self, host, port):
        """解析域名"""

        def callback(ip, port):
            """解析成功后, 开始发送find_node"""
            self.findNode((ip, port))

        def errback(failure, host, port):
            """解析失败, 再继续解析, 直到成功为止"""
            self.resolve(host, port)

        d = reactor.resolve(host)
        d.addCallback(callback, port)
        d.addErrback(errback, host, port)

    def joinFailHandle(self):
        """加入DHT网络失败, 再继续加入, 直到加入成功为止"""
        if len(self.table) == 0:
            self.joinNetwork()

    def refreshRoutingTable(self):
        """
        刷新路由表

        遇到不"新鲜"的bucket时, 随机选一个node, 发送find_node
        """
        for bucket in self.table:
            if bucket.isFresh():
                continue

            node = bucket.random()
            if node is None:
                continue  # 如果该bucket无node, 继续下一个

            reactor.callLater(const.NEXT_FIND_NODE_INTERVAL, self.findNode, (node.ip, node.port))

    def rejoinNetwork(self):
        """
        防止find_node请求停止而打造. 停止后, 再重新加入DHT网络
        """
        if (self.lastFind - time.time()) > const.FIND_TIMEOUT:
            self.joinNetwork()
