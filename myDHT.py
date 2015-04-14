#!/usr/bin/env python2.7

import socket
import struct
import threading
import time

from random import randint
import hashlib
from bencode import bencode, bdecode
from nodes import decode_nodes, encode_nodes, Nodes, KNode

from settings import *

BOOTSTRAP_NODES = (
    ("54.64.84.43", 8888),
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


class DHTClient(threading.Thread):
    def __init__(self, max_node_qsize):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.max_node_qsize = max_node_qsize
        self.nid = random_id()
        self.nodes = Nodes()

    def send_krpc(self, msg, address):
        try:
            self.ufd.sendto(bencode(msg), address)
        except Exception as msg:
            print("DHTClient.send_krpc error: ", msg)

    def send_find_node(self, address, nid=None, target_id=random_id()):
        nid = self.nid
        tid = entropy(TID_LENGTH)
        msg = {
            't': tid,
            'y': 'q',
            'q': 'find_node',
            'a': {
                'id': nid,
                'target': target_id
            }
        }
        self.send_krpc(msg, address)

    def join_DHT(self):
        for address in BOOTSTRAP_NODES:
            self.send_find_node(address)

    def send_ping(self, address, nid):
        tid = entropy(TID_LENGTH)
        msg = {
            't': tid,
            'y': 'q',
            'q': 'ping',
            'a': {
                'id': self.nid,
            }
        }
        self.send_krpc(msg, address)


    def process_find_node_response(self, msg, address): 
        nodes = deocde_nodes(msg['r']['nodes'])
        for node in nodes:
            (nid, ip, port) = node
            if len(nid) != 20: continue
            if ip == self.bind_ip: continue
            n = KNode(nid, ip, port)
            self.nodes.store(n)


class DHTServer(DHTClient):
    def __init__(self, master, bind_ip, bind_port, max_node_qsize):
        DHTClient.__init__(self, max_node_qsize)
        self.master = master
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        
        self.process_request_actions = {
            'ping': self.on_ping_request,
            'find_node': self.on_find_node_request,
            'get_peers': self.on_get_peers_request, 
            'announce_peer': self.on_announce_peer_request,
        }

        self.ufd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.ufd.bind((self.bind_ip, self.bind_port))

    def run(self):
        self.join_DHT()
        while True:
            try:
                (data, address) = self.ufd.recvfrom(65536) 
                msg = bdecode(data)
                print(address)
                self.on_message(msg, address) 
            except Exception as msg:
                if(DEBUG): print("DHTServer.run error: ", msg)

    def refresh_id(self, nid, address):
        (ip, port) = address
        n = KNode(nid, ip, port)
        self.nodes.store(n)

    def on_message(self, msg, address):
        try:
            if msg['y'] == 'r':
                self.refresh_id(msg['r']['id'], address)
                if 'nodes' in msg['r']:
                    self.process_find_node_response(msg, address)
            elif msg['y'] == 'q':
                try:
                    self.process_request_actions[msg['q']](msg, address)
                except KeyError as msg:
                    if (DEBUG): print("on_message'r' error: ", msg)
                    self.play_dead(msg, address)
        except KeyError:
            if (DEBUG): print("on_message error: ", msg)

    def on_ping_request(self, msg, address):
        nid = msg.nid
        tid = msg['t']
        msg = {
            't': tid,
            'y': 'r',
            'r': {
                'id': nid,
             }    
        }
        self.send_krpc(msg, address)

    def on_find_node_request(self, msg, address):
        pass

    def on_get_peers_request(self, msg, address):
        pass

    def on_announce_peer_request(self, msg, address):
        pass


class Master:
    def log(self, data, address=None):
        print("%s from %s:%s" % (
            str(data), address[0], address[1]
        ))


if __name__ == '__main__':
    dht = DHTServer(Master(), "0.0.0.0", 6882, max_node_qsize=200)
    dht.start()
    while True:
        time.sleep(1)
