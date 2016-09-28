#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-27

import json
import struct
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import connectionDone
from util.log import Logger


class TcpClientProtocol(Protocol):
    def __init__(self):
        self._data = ''

    def dataReceived(self, data):
        self._data += data
        while len(self._data) > 12:
            cmd, msg_len, _ = struct.unpack('III', self._data[:12])
            if msg_len > len(self._data) - 12:
                return
            body_data = self._data[12:12 + msg_len]
            self._data = self._data[12 + msg_len:]
            param = json.loads(body_data, separators=(',', ':'))
            Logger.debug("====%06d recv: 0x08%X %s" % (self.player.uid, cmd, body_data))
            self.player.on_msg(cmd, param)

    def sendMsg(self, cmd, param):
        if self.transport and self.connected:
            body = json.dumps(param)
            header = struct.pack('III', cmd, len(body), 0)
            try:
                self.transport.write(header + body)
                Logger.debug("====%06d send：0x08%X %s" % (self.player.uid, cmd, body))
                return True
            except Exception, e:
                Logger.exception()
                return False
        else:
            Logger.info('not connect, cannot send msg 0x%06x|%s' % (cmd, param))
            return False

    def stop(self):
        Logger.info('active close connect')
        self.transport.loseConnection()

    def connectionMade(self):
        self._data = ''
        self.player.run()

    def connectionLost(self, reason=connectionDone):
        self.factory.done(reason)


class TcpClientFactory(ClientFactory):
    protocol = TcpClientProtocol

    def __init__(self, deferred, player):
        self.deferred = deferred
        self.player = player

    def done(self, reason):
        if self.deferred:
            d, self.deferred = self.deferred, None
            d.callback(reason)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred:
            d, self.deferred = self.deferred, None
            d.errback(reason)

    def buildProtocol(self, addr):
        p = ClientFactory.buildProtocol(self, addr)
        p.player = self.player
        self.player.protocol = p
        return p
