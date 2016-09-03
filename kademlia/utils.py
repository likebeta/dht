#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import struct
import random
import hashlib


def entropy(length):
    """随机生成字符串"""
    s = ""
    for i in range(length):
        s += chr(random.randint(0, 255))
    return s


def intify(hstr):
    """把20字节的hash值转换为数字"""
    assert len(hstr) == 20
    return long(hstr.encode('hex'), 16)


def sha1_encode(s):
    h = hashlib.sha1()
    h.update(entropy(20))
    return h.hexdigest()


def new_node_id():
    """生成node ID"""
    h = hashlib.sha1()
    h.update(entropy(20))
    return h.digest()


def ipv4_to_int4(ip):
    """把ipv4转换为4字节整型"""
    hexn = ''.join(["%02X" % long(i) for i in ip.split('.')])
    return long(hexn, 16)


def int4_to_ipv4(n):
    """把4字节整型转换为ipv4"""
    d = 256 * 256 * 256
    q = []
    while d > 0:
        m, n = divmod(n, d)
        q.append(str(m))
        d /= 256
    return '.'.join(q)


def decode_nodes(nodes):
    """
    把收到的nodes转成list
    数据格式: [(node ID, ip, port), (node ID, ip, port), (node ID, ip, port).... ]
    """
    n = []
    node_count = len(nodes) / 26
    if node_count > 0:
        nodes = struct.unpack("!" + "20sIH" * node_count, nodes)
        for i in xrange(node_count):
            nid, ip, port = nodes[i * 3], int4_to_ipv4(nodes[i * 3 + 1]), nodes[i * 3 + 2]
            n.append((nid, ip, port))
    return n


def encode_nodes(nodes):
    """
    与 decode_nodes 相反
    """
    if not nodes:
        return ''

    n = []
    for node in nodes:
        n.extend([node.nid, ipv4_to_int4(node.ip), node.port])
    return struct.pack("!" + "20sIH" * len(nodes), *n)
