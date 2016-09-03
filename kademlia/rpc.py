#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import socket
import bencode
from twisted.internet import protocol


class KRPC(protocol.DatagramProtocol):
    def __init__(self):
        self.actionSwitch = {
            "r": self.handle_response,
            "q": self.handle_query,
            "e": self.handle_error,
        }

        self.queryActions = {
            "ping": self.on_ping,
            "find_node": self.on_find_node,
            "get_peers": self.on_get_peers,
            "announce_peer": self.on_announce_peer,
        }

    def datagramReceived(self, data, address):
        """
        数据接收
        """
        try:
            res = bencode.bdecode(data)
            self.actionSwitch[res["y"]](res, address)
        except(bencode.BTL.BTFailure, KeyError):
            pass

    def sendMsg(self, msg, address):
        """
        发送数据
        """
        try:
            self.transport.write(bencode.bencode(msg), address)
        except socket.error:
            pass

    def send_query(self, msg, address):
        """发送请求类型数据"""
        self.sendMsg(msg, address)

    def send_response(self, msg, address):
        """发送回应类型数据"""
        self.sendMsg(msg, address)

    def handle_query(self, res, address):
        """
        收到请求类型的数据后, 智能调用DHT服务器端相关处理函数
        """
        try:
            self.queryActions[res["q"]](res, address)
        except KeyError:
            pass

    def handle_response(self, res, address):
        """
        收到请求类型的数据, 直接调用处理find_node回应的方法即可,
        因为爬虫客户端只实现了find_node请求.
        """
        try:
            self.on_ack_find_node(res)
        except KeyError:
            pass

    def handle_error(self, res, address):
        """收到错误回应, 忽略"""
        pass
