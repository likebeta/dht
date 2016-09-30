#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-27

import struct
import hashlib
import bencode
from twisted.internet.protocol import Protocol
from twisted.internet.protocol import ClientFactory
from util.log import Logger
from dht.kademlia import utils

BT_PROTOCOL = 'BitTorrent protocol'

MSG_CHOKE = 0
MSG_UNCHOKE = 1
MSG_INTERESTED = 2
MSG_NOT_INTERESTED = 3
MSG_HAVE = 4
MSG_BITFIELD = 5
MSG_REQUEST = 6
MSG_PIECE = 7
MSG_CANCEL = 8
MSG_PORT = 9

MSG_EXT_ID = 20
EXT_HANDSHAKE_ID = 0

MSG_TYPE_REQUEST = 0
MSG_TYPE_DATA = 1
MSG_TYPE_REJECT = 2

DEBUG = False


class TcpClientProtocol(Protocol):
    def __init__(self, info_hash, peer_id=None):
        self.has_handshake = False
        self.metadata = ''
        self.metadata_size = 0
        self.ut_metadata = 0
        self._data = ''
        self.info_hash = info_hash
        if peer_id is None:
            peer_id = utils.random_node_id()
        self.peer_id = peer_id

    def dataReceived(self, data):
        try:
            self._data += data
            if not self.has_handshake:
                self.check_handshake()

            if self.has_handshake:
                while len(self._data) > 4:
                    length = struct.unpack('>I', self._data[:4])[0]
                    if length == 0:
                        if DEBUG:
                            Logger.debug("==== RECV: keep alive")
                        self.on_keep_alive()
                    else:
                        if length > len(self._data) - 4:
                            return

                        data, self._data = self._data[4:4 + length], self._data[4 + length:]
                        cmd, data = ord(data[0]), data[1:]
                        if DEBUG:
                            Logger.debug("==== RECV:", cmd, len(data), repr(data))
                        self.on_message(cmd, data)
        except Exception, e:
            Logger.exception(repr(data))
            self.transport.loseConnection()

    def sendPacket(self, data):
        if self.transport and self.connected:
            try:
                self.transport.write(data)
                if DEBUG:
                    Logger.debug('==== SEND:', data)
                return True
            except Exception, e:
                Logger.exception()
                self.transport.loseConnection()
                return False
        else:
            Logger.info('not connect, cannot send msg', data)
            return False

    def sendMsg(self, data):
        header = struct.pack(">I", len(data))
        self.sendPacket(header + data)

    def stop(self):
        self.transport.loseConnection()

    def connectionMade(self):
        self._data = ''
        self.send_handshake()

    def send_handshake(self):
        """
        握手：handshake: <pstrlen><pstr><reserved><info_hash><peer_id>
          1. pstrlen: <pstr>的字符串长度，单个字节。
          2. pstr: 协议的标识符，字符串类型。
          3. reserved: 8个保留字节。当前的所有实现都使用全0.这些字节里面的每一个字节都可以用来改变协议的行为。
             来自Bram的邮件建议应该首先使用后面的位，以便可以使用前面的位来改变后面位的意义。
          4. info_hash: 元信息文件中info键(key)对应值的20字节SHA1哈希。这个info_hash和在tracker请求中info_hash是同一个。
          5. peer_id: 用于唯一标识客户端的20字节字符串。这个peer_id通常跟在tracker请求中传送的
             peer_id相同(但也不尽然，例如在Azureus，就有一个匿名选项)。
        握手是一个必需的报文，并且必须是客户端发送的第一个报文。该握手报文的长度是(49+len(pstr))字节。
        在BitTorrent协议1.0版本，pstrlen = 19, pstr = 'BitTorrent protocol'
        """
        bt_header = chr(len(BT_PROTOCOL)) + BT_PROTOCOL
        reserved = "\x00\x00\x00\x00\x00\x10\x00\x00"
        packet = bt_header + reserved + self.info_hash + self.peer_id
        self.sendPacket(packet)

    def send_ext_handshake(self):
        data = chr(MSG_EXT_ID) + chr(EXT_HANDSHAKE_ID) + bencode.bencode({"m": {"ut_metadata": 1}})
        self.sendMsg(data)

    def send_ext_metadata(self, piece=0):
        data = chr(MSG_EXT_ID) + chr(self.ut_metadata) + bencode.bencode({"msg_type": 0, "piece": piece})
        self.sendMsg(data)

    def on_message(self, cmd, data):
        if cmd == MSG_CHOKE:
            self.on_choke()
        elif cmd == MSG_UNCHOKE:
            self.on_unchoke()
        elif cmd == MSG_INTERESTED:
            self.on_interested()
        elif cmd == MSG_NOT_INTERESTED:
            self.on_not_interested()
        elif cmd == MSG_HAVE:
            self.on_have(data)
        elif cmd == MSG_BITFIELD:
            self.on_bitfield(data)
        elif cmd == MSG_REQUEST:
            self.on_request(data)
        elif cmd == MSG_PIECE:
            self.on_piece(data)
        elif cmd == MSG_CANCEL:
            self.on_cancel(data)
        elif cmd == MSG_PORT:
            self.on_port(data)
        elif cmd == MSG_EXT_ID:
            self.on_ext_message(data)

    def check_handshake(self):
        total = 49 + len(BT_PROTOCOL)
        if len(self._data) < total:
            return False

        data, self._data = self._data[:total], self._data[total:]
        try:
            bt_header_len = ord(data[0])
            if bt_header_len != len(BT_PROTOCOL):
                return False
        except TypeError:
            return False

        offset = 1
        bt_header = data[offset:bt_header_len + offset]
        if bt_header != BT_PROTOCOL:
            return False

        offset += bt_header_len
        reserved = data[offset:offset + 8]
        # check extended messaging
        if reserved[5] != '\x10':
            return False

        offset += 8
        _info_hash = data[offset:offset + 20]
        if _info_hash != self.info_hash:
            return False

        self.has_handshake = True
        self.send_ext_handshake()
        return True

    def on_keep_alive(self):
        """
        keep-alive: <len=0000>
        keep-alive消息是一个0字节的消息，将length prefix设置成0。没有message ID和payload。
        如果peers在一个固定时间段内没有收到任何报文(keep-alive或其他任何报文)，那么peers应该关掉这个连接，
        因此如果在一个给定的时间内没有发出任何命令的话，peers必须发送一个keep-alive报文保持这个连接激活。
        通常情况下，这个时间是2分钟。
        """

    def on_choke(self):
        """
        choke: <len=0001><id=0>
        choke报文长度固定，并且没有payload
        """

    def on_unchoke(self):
        """
        unchoke: <len=0001><id=1>
        unchoke报文长度固定，并且没有payload
        """

    def on_interested(self):
        """
        interested: <len=0001><id=2>
        interested报文长度固定，并且没有payload
        """

    def on_not_interested(self):
        """
        not interested: <len=0001><id=3>
        not interested报文长度固定，并且没有payload
        """

    def on_have(self, data):
        """
        have: <len=0005><id=4><piece index>
        have报文长度固定。payload是piece(片)的从零开始的索引，该片已经成功下载并且通过hash校验。
        实现者注意：实际上，一些客户端必须严格实现该定义。因为peers不太可能下载他们已经拥有的piece(片)，
        一个peer不应该通知另一个peer它拥有一个piece(片)，如果另一个peer拥有这个piece(片)。
        最低限度”HAVE suppresion”会使用have报文数量减半，总的来说，大致减少25-35%的HAVE报文。
        同时，给一个拥有piece(片)的peer发送HAVE报文是值得的，因为这有助于决定哪个piece是稀缺的。
        一个恶意的peer可能向其他的peer广播它们不可能下载的piece(片)。
        Due to this attempting to model peers using this information is a bad idea
        """

    def on_bitfield(self, data):
        """
        bitfield: <len=0001+X><id=5><bitfield>
        bitfield报文可能仅在握手序列发送之后，其他消息发送之前立即发送。
        它是可选的，如果一个客户端没有piece(片)，就不需要发送该报文。
        bitfield报文长度可变，其中x是bitfield的长度。payload是一个bitfield，
        该bitfield表示已经成功下载的piece(片)。第一个字节的高位相当于piece索引0。
        设置为0的位表示一个没有的piece，设置为1的位表示有效的和可用的piece。末尾的冗余位设置为0。
        长度不对的bitfield将被认为是一个错误。如果客户端接收到长度不对的bitfield或者bitfield有任一冗余位集，
        它应该丢弃这个连接。
        """

    def on_request(self, data):
        """
        request: <len=0013><id=6><index><begin><length>
        request报文长度固定，用于请求一个块(block)。
        payload包含如下信息：
          1. index: 整数，指定从零开始的piece索引。
          2. begin: 整数，指定piece中从零开始的字节偏移。
          3. length: 整数，指定请求的长度。
        """

    def on_piece(self, data):
        """
        piece: <len=0009+X><id=7><index><begin><block>
        piece报文长度可变，其中x是块的长度。
        payload包含如下信息：
          1. index: 整数，指定从零开始的piece索引。
          2. begin: 整数，指定piece中从零开始的字节偏移。
          3. block: 数据块，它是由索引指定的piece的子集。
        """

    def on_cancel(self, data):
        """
        cancel: <len=0013><id=8><index><begin><length>
        cancel报文长度固定，用于取消块请求。playload与request报文的playload相同。一般情况下用于结束下载。
        """

    def on_port(self, data):
        """
        port: <len=0003><id=9><listen-port>
        port报文由新版本的Mainline发送，新版本Mainline实现了一个DHT tracker。
        该监听端口是peer的DHT节点正在监听的端口。这个peer应该插入本地路由表(如果支持DHT tracker的话)
        """

    def on_ext_message(self, data):
        ext_id = ord(data[0])
        if ext_id == EXT_HANDSHAKE_ID:
            self.on_ext_handshake(data[1:])
        else:
            self.on_ext_metadata(data[1:])

    def on_ext_handshake(self, data):
        info = bencode.bdecode(data)
        self.metadata_size = info['metadata_size']
        self.ut_metadata = info['m']['ut_metadata']
        self.send_ext_metadata(0)

    def on_ext_metadata(self, data):
        sep = data.index('ee') + 2
        header = bencode.bdecode(data[:sep])
        if header['msg_type'] != 1:
            Logger.info('error msg_type', header['msg_type'])
            self.stop()
            return

        body = data[sep:]
        self.metadata += body
        if len(self.metadata) < self.metadata_size:
            self.send_ext_metadata(header['piece'] + 1)
        else:
            if self.check_metadata():
                info = bencode.bdecode(self.metadata)
                self.stop()
                self.factory.done(info)

    def check_metadata(self):
        info_hash = hashlib.sha1(self.metadata).digest()
        return info_hash == self.info_hash


class TcpClientFactory(ClientFactory):
    protocol = TcpClientProtocol

    def __init__(self, deferred, info_hash, peer_id=None):
        self.deferred = deferred
        self.info_hash = info_hash
        self.peer_id = peer_id

    def done(self, info):
        if self.deferred:
            d, self.deferred = self.deferred, None
            d.callback(info)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred:
            d, self.deferred = self.deferred, None
            d.errback(reason)

    def clientConnectionLost(self, connector, reason):
        if self.deferred:
            d, self.deferred = self.deferred, None
            d.errback(reason)

    def buildProtocol(self, addr):
        p = self.protocol(self.info_hash, self.peer_id)
        p.factory = self
        return p
