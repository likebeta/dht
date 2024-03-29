#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import time
import const
import utils
import random
import bisect


class KNode(object):
    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port

    def __eq__(self, other):
        return self.nid == other.nid

    def __ne__(self, other):
        return self.nid != other.nid


class KBucket(object):
    def __init__(self, min_id, max_id):
        """
        min和max就是该bucket负责的范围, 比如该bucket的min:0, max:16的话,
        那么存储的node的utils.intify(nid)值均为: 0到15, 那16就不负责, 这16将会是该bucket后面的bucket的min值.
        nodes属性就是个列表, 存储node. last_access_ts代表最后访问时间, 因为协议里说到,
        当该bucket负责的node有请求, 回应操作; 删除node; 添加node; 更新node; 等这些操作时,
        那么就要更新该bucket, 所以设置个last_access_ts属性, 该属性标志着这个bucket的"新鲜程度".
        用linux话来说, touch一下. 这个用来便于后面说的定时刷新路由表.
        """
        self.min_id = min_id
        self.max_id = max_id
        self.nodes = []
        self.last_access_ts = time.time()

    def append(self, node):
        if len(node.nid) != 20:
            return

        # 如果已在该bucket里, 替换掉
        if node in self:
            self.remove(node)
            self.nodes.append(node)
        else:
            # 不在该bucket并且未满, 插入
            if len(self) < const.K:
                self.nodes.append(node)
            # 满了, 抛出异常, 通知上层代码进行拆表
            else:
                raise BucketFull

        # 替换/添加node都要更改bucket最后访问时间
        self.touch()

    def remove(self, node):
        """删除节点"""
        self.nodes.remove(node)

    def touch(self):
        """更新bucket最后访问时间"""
        self.last_access_ts = time.time()

    def random(self):
        """随机选择一个node"""
        if len(self.nodes) == 0:
            return None
        return self.nodes[random.randint(0, len(self.nodes) - 1)]

    def is_fresh(self):
        """bucket是否新鲜"""
        return (time.time() - self.last_access_ts) > const.BUCKET_LIFETIME

    def in_range(self, target):
        """目标node ID是否在该范围里"""
        return self.min_id <= utils.intify(target) < self.max_id

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, node):
        return node in self.nodes

    def __iter__(self):
        for node in self.nodes:
            yield node

    def __lt__(self, target):
        """
        为bisect打造, 目的是快速定位bucket的所在索引, 不需一个个循环.
        虽然一个路由表最多只能存储158个bucket, 不过追求极限是程序员的美德之一.
        """
        return self.max_id <= target


class BucketFull(Exception):
    pass


class KTable(object):
    def __init__(self, nid=None):
        if nid is None:
            nid = utils.random_node_id()
        self.nid = nid
        self.buckets = [KBucket(0, 2 ** 160)]

    def touch_bucket(self, target):
        """
        更新指定node所在bucket最后访问时间
        """
        try:
            self.buckets[self.bucket_index(target)].touch()
        except IndexError:
            pass

    def append(self, node):
        if self.nid == node.nid:
            return  # 不存储自己

        index = self.bucket_index(node.nid)
        bucket = self.buckets[index]
        try:
            bucket.append(node)
        except BucketFull:
            # 拆表前, 先看看自身node ID是否也在该bucket里, 如果不在, 终止
            if not bucket.in_range(self.nid):
                return

            self.split_bucket(index)
            self.append(node)

    def find_close_nodes(self, target, n=const.K):
        """
        找出离目标node ID或infohash最近的前n个node
        """
        nodes = []
        if len(self.buckets) == 0:
            return nodes

        index = self.bucket_index(target)
        try:
            nodes = self.buckets[index].nodes
            min_index = index - 1
            max_index = index + 1

            while len(nodes) < n and (min_index >= 0 or max_index < len(self.buckets)):
                # 如果还能往前走
                if min_index >= 0:
                    nodes.extend(self.buckets[min_index].nodes)

                # 如果还能往后走
                if max_index < len(self.buckets):
                    nodes.extend(self.buckets[max_index].nodes)

                min_index -= 1
                max_index += 1

            return nodes[:n]
        except IndexError:
            return nodes
        finally:
            # 按异或值从小到大排序
            num = utils.intify(target)
            nodes.sort(lambda a, b: cmp(num ^ utils.intify(a.nid), num ^ utils.intify(b.nid)))

    def bucket_index(self, target):
        """
        定位指定node ID 或 infohash 所在的bucket的索引
        """
        return bisect.bisect_left(self.buckets, utils.intify(target))

    def split_bucket(self, index):
        """
        index是待拆分的bucket(old bucket)的所在索引值. 
        假设这个old bucket的min:0, max:16. 拆分该old bucket的话, 分界点是8, 然后把old bucket的max改为8, min还是0. 
        创建一个新的bucket, new bucket的min=8, max=16.
        然后根据的old bucket中的各个node的nid, 看看是属于哪个bucket的范围里, 就装到对应的bucket里.
        new bucket的索引值就在old bucket后面, 即index+1, 把新的bucket插入到路由表里.
        """
        old = self.buckets[index]
        point = old.max_id - (old.max_id - old.min_id) / 2
        new = KBucket(point, old.max_id)
        old.max_id = point
        self.buckets.insert(index + 1, new)
        for node in old.nodes[:]:
            if new.in_range(node.nid):
                new.append(node)
                old.remove(node)

    def __iter__(self):
        for bucket in self.buckets:
            yield bucket

    def __len__(self):
        length = 0
        for bucket in self:
            length += len(bucket)
        return length

    def __contains__(self, node):
        try:
            index = self.bucket_index(node.nid)
            return node in self.buckets[index]
        except IndexError:
            return False
