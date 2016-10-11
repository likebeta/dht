#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import socket
import bencode
from util.log import Logger
from twisted.internet import protocol

DEBUG = False


class KRPC(protocol.DatagramProtocol):
    def __init__(self):
        self.actionSwitch = {
            "r": self.handle_response,
            "q": self.handle_query,
            "e": self.handle_error,
        }

        self.queryActions = {
            # "ping": self.on_ping,
            # "find_node": self.on_find_node,
            "get_peers": self.on_get_peers,
            "announce_peer": self.on_announce_peer,
            # "vote": self.on_vote,
            # "v": self.on_version,
        }

    def datagramReceived(self, data, address):
        """
        数据接收
        """
        try:
            msg = bencode.bdecode(data)
            if DEBUG:
                Logger.debug('==== RECV UDP:', msg)
            self.actionSwitch[msg["y"]](msg, address)
        except(bencode.BTL.BTFailure, KeyError):
            if DEBUG:
                Logger.exception()

    def sendMsg(self, msg, address):
        """
        发送数据
        """
        try:
            if DEBUG:
                Logger.debug('==== SEND UDP:', msg)
            data = bencode.bencode(msg)
            self.transport.write(data, address)
        except socket.error:
            if DEBUG:
                Logger.exception()

    def send_query(self, msg, address):
        """发送请求类型数据"""
        self.sendMsg(msg, address)

    def send_response(self, msg, address):
        """发送回应类型数据"""
        self.sendMsg(msg, address)

    def handle_query(self, msg, address):
        """
        收到请求类型的数据后, 智能调用DHT服务器端相关处理函数
        """
        try:
            self.queryActions[msg["q"]](msg, address)
        except KeyError:
            self.error(msg, address)

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

    def error(self, msg, address):
        try:
            tid = msg["t"]
            msg = {
                "t": tid,
                "y": "e",
                "e": [202, "Server Error"]
            }
            self.send_response(msg, address)
        except KeyError:
            pass
