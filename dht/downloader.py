#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-13

import math
import time
import struct
import socket
import bencode
from util.log import Logger
from dht.kademlia import utils


class Downloader(object):
    BT_PROTOCOL = "BitTorrent protocol"
    BT_MSG_ID = 20
    EXT_HANDSHAKE_ID = 0

    @classmethod
    def get_torrent(cls, info_hash, address=None):
        pass

    @classmethod
    def download_from_third_cache(cls, info_hash):
        # upper_hash = info_hash.upper()
        pass

    @classmethod
    def __url_from_xunlei(cls, info_hash):
        return 'http://bt.box.n0808.com/%s/%s/%s.torrent' % (info_hash[:2], info_hash[-3:-1], info_hash)

    @classmethod
    def __url_from_vuze(cls, info_hash):
        return 'http://magnet.vuze.com/magnetLookup?hash=' + info_hash

    @classmethod
    def __url_from_torrage(cls, info_hash):
        return 'http://torrage.com/torrent/%s.torrent' % info_hash

    @classmethod
    def __url_from_torcache(cls, info_hash):
        # see other http://torrage.info
        return 'http://torrage.info/torrent.php?h=%s' % info_hash

    @classmethod
    def __url_from_zoink(cls, info_hash):
        return 'http://zoink.it/torrent/%s.torrent' % info_hash

    @classmethod
    def download_metadata(cls, info_hash, address, peer_id=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(5)
            sock.connect(address)

            # handshake
            cls.send_handshake(sock, info_hash, peer_id)
            packet = sock.recv(4096)

            # check handshake
            if not cls.check_handshake(packet, info_hash):
                return

            # ext handshake
            cls.send_ext_handshake(sock)
            packet = sock.recv(4096)

            # get ut_metadata and metadata_size
            ut_metadata, metadata_size = cls.get_ut_metadata(packet), cls.get_metadata_size(packet)

            # request each piece of metadata
            metadata = []
            for piece in range(int(math.ceil(metadata_size / (16.0 * 1024)))):
                cls.request_metadata(sock, ut_metadata, piece)
                packet = cls.recvall(sock, 5)
                metadata.append(packet[packet.index("ee") + 2:])

            metadata = ''.join(metadata)
            try:
                info = bencode.bdecode(metadata)
                Logger.info('-----------------Fetched', info["name"], "size: ", len(metadata))
                return info["name"], metadata
            except:
                pass
        except socket.error:
            pass
        except Exception, e:
            import traceback
            traceback.print_exc()
            pass
        finally:
            sock.close()

    @classmethod
    def recvall(cls, sock, timeout=5):
        sock.setblocking(0)
        total_data = []
        begin = time.time()

        while True:
            time.sleep(0.05)
            if total_data and time.time() - begin > timeout:
                break
            elif time.time() - begin > timeout * 2:
                break
            try:
                data = sock.recv(1024)
                if data:
                    total_data.append(data)
                    begin = time.time()
            except socket.error, e:
                if e.errno != 11:  # [Errno 11] Resource temporarily unavailable
                    break
            except Exception:
                import traceback
                traceback.print_exc()
                pass
        return ''.join(total_data)

    @classmethod
    def send_packet(cls, sock, msg):
        sock.send(msg)

    @classmethod
    def send_message(cls, sock, msg):
        msg_len = struct.pack(">I", len(msg))
        cls.send_packet(sock, msg_len + msg)

    @classmethod
    def send_handshake(cls, sock, info_hash, peer_id):
        bt_header = chr(len(cls.BT_PROTOCOL)) + cls.BT_PROTOCOL
        ext_bytes = "\x00\x00\x00\x00\x00\x10\x00\x00"
        if peer_id is None:
            peer_id = utils.random_node_id()
        packet = bt_header + ext_bytes + info_hash + peer_id
        cls.send_packet(sock, packet)

    @classmethod
    def check_handshake(cls, packet, self_infohash):
        try:
            bt_header_len, packet = ord(packet[0]), packet[1:]
            if bt_header_len != len(cls.BT_PROTOCOL):
                return False
        except TypeError:
            return False

        bt_header, packet = packet[:bt_header_len], packet[bt_header_len:]
        if bt_header != cls.BT_PROTOCOL:
            return False

        if packet[5] != '\x10':
            return False

        packet = packet[8:]

        infohash = packet[:20]
        if infohash != self_infohash:
            return False

        return True

    @classmethod
    def send_ext_handshake(cls, sock):
        msg = chr(cls.BT_MSG_ID) + chr(cls.EXT_HANDSHAKE_ID) + bencode.bencode({"m": {"ut_metadata": 1}})
        cls.send_message(sock, msg)

    @classmethod
    def request_metadata(cls, sock, ut_metadata, piece):
        """bep_0009"""
        msg = chr(cls.BT_MSG_ID) + chr(ut_metadata) + bencode.bencode({"msg_type": 0, "piece": piece})
        cls.send_message(sock, msg)

    @classmethod
    def get_ut_metadata(cls, data):
        ut_metadata = "_metadata"
        index = data.index(ut_metadata) + len(ut_metadata) + 1
        return int(data[index])

    @classmethod
    def get_metadata_size(cls, data):
        metadata_size = "metadata_size"
        start = data.index(metadata_size) + len(metadata_size) + 1
        data = data[start:]
        return int(data[:data.index("e")])


if __name__ == '__main__':
    with open('../info_hash.log.sorted') as f:
        for line in f:
            ip, port, infohash = line.split()
            result = Downloader.download_metadata(infohash[:40].decode('hex'), (ip, int(port)))
            if result:
                with open(result[0], 'w') as fp:
                    fp.write(result[1])
