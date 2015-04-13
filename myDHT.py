#!/usr/bin/env python3.4

import socket
import struct
import hashlib
from random import randint
import threading
import time
import bencode
import collections

BOOTSTRAP_NODES = (
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("router.utorrent.com", 6881),
)
TID_LENGTH = 2

def entropy(length):
    return "".join(chr(randint(0, 255)) for _ in range(length))

def random_id():
    h = hashlib.sha1()
    h.update(entropy(20))
    return h.digest()


def decode_nodes(nodes):
    n = []
    length = len(nodes)
    if length % 26 != 0:
        return n
    for i in range(0, lengthn, 26):
        nid = nodes[i:i+20] 
        ip = socket.inet_ntoa(nodes[i+20:i+24])
        port = struct.unpack("!H", nodes[i+24:i+26])[0]
        n.append((nid, ip, port))
    return n


class KNode:
    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port


class DHTClient(threading.Thread):
    def __init__(self, max_node_qsize):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.max_node_qsize = max_node_qsize
        self.nid = random_id()
        self.nodes = collections.deque(maxlen=max_node_qsize)

    def send_krpc(self, msg, address):
        try:
            self.ufd.sendto(bencode(msg), address)
        except Exception:
            pass

    def send_find_node(self, address, nid=None):
        nid = self.nid
        tid = entropy(TID_LENGTH)
        msg = {
            't': tid,
            'y': 'q',
            'q': 'find_node',
            'a': {
                'id': nid,
                'target': random_id()
            }
        }
        self.send_krpc(msg, address)

    def join_DHT(self):
        for address in BOOTSTRAP_NODES:
            self.send_find_node(address)


class DHTServer(DHTClient):
    def __init__(self, master, bind_ip, bind_port, max_node_qsize):
        DHTClient.__init__(self, max_node_qsize)
        self.master = master
        self.bind_ip = bind_ip
        self.bind_port = bind_port

        self.ufd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ufd.bind((self.bind_ip, self.bind_port))

    def run(self):
        while True:
            try:
                self.join_DHT()
                (data, address) = self.ufd.recvfrom(65536) 
                msg = bdecode(data)
                self.master.log(data, (address, port))
            except Exception:
                pass

class Master:
    def log(self, data, address=None):
        print("%s from %s:%s" % (
            str(data), address[0], address[1]
        ))


if __name__ == '__main__':
    dht = DHTServer(Master(), "0.0.0.0", 6882, 200)
    dht.start()
    while True:
        time.sleep(1)
