#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import time
import const
import utils
from rpc import KRPC
from table import KNode
from table import KTable
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
        self.table = KTable()
        self.last_find_ts = time.time()
        timer(const.REFRESH_INTERVAL, self.refresh_routing_table)
        timer(const.FIND_TIMEOUT, self.rejoin_network)

    def find_node(self, *addresses):
        """
        DHT爬虫的客户端至少要实现find_node.
        此方法最主要的功能就是不停地让更多人认识自己.
        爬虫只需认识(160^2) * K 个节点即可
        """
        for address in addresses:
            tid = utils.entropy(const.TID_LENGTH)
            msg = {
                "t": tid,
                "y": "q",
                "q": "find_node",
                "a": {"id": self.table.nid, "target": self.table.nid}
            }
            self.send_query(msg, address)

    def on_ack_find_node(self, res):
        """
        处理find_node回应数据
        """
        try:
            self.table.touch_bucket(res["r"]["id"])

            nodes = utils.decode_nodes(res["r"]["nodes"])
            addresses = set()
            for node in nodes:
                nid, ip, port = node
                if nid == self.table.nid:
                    continue  # 不存自己
                self.table.append(KNode(nid, ip, port))
                addresses.add((ip, port))

            if addresses:
                self.last_find_ts = time.time()  # 最后请求时间
                # 等待NEXT_FIND_NODE_INTERVAL时间后, 进行下一个find_node
                reactor.callLater(const.NEXT_FIND_NODE_INTERVAL, self.find_node, *addresses)
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
            self.find_node((ip, port))

        def errback(failure, host, port):
            """解析失败, 再继续解析, 直到成功为止"""
            self.resolve(host, port)

        d = reactor.resolve(host)
        d.addCallback(callback, port)
        d.addErrback(errback, host, port)

    def join_fail_handle(self):
        """加入DHT网络失败, 再继续加入, 直到加入成功为止"""
        if len(self.table) == 0:
            self.join_network()

    def refresh_routing_table(self):
        """
        遇到不新鲜的bucket时, 随机选一个node, 发送find_node
        """
        addresses = set()
        for bucket in self.table:
            if bucket.is_fresh():
                continue

            node = bucket.random()
            if node is None:
                continue  # 如果该bucket无node, 继续下一个

            addresses.add((node.ip, node.port))
        if addresses:
            reactor.callLater(const.NEXT_FIND_NODE_INTERVAL, self.find_node, *addresses)

    def rejoin_network(self):
        """
        防止find_node请求停止而打造. 停止后, 再重新加入DHT网络
        """
        if (self.last_find_ts - time.time()) > const.FIND_TIMEOUT:
            self.join_network()
