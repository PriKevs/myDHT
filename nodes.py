from collections import deque
from struct import unpack, pack
from socket import inet_ntoa, inet_aton
import math
import binascii
import threading

from settings import *

IDLEN = 20

def encode_nodes(nodelist):
    n = b'' 
    print(nodelist)
    for node in nodelist:
        byte_nid = node.nid
        byte_ip = inet_aton(node.ip)
        byte_port = pack('!H', node.port)
        n = n + (byte_nid + byte_ip + byte_port)
        if DEBUG: print(n)
    return n

def decode_nodes(nodes):
    n = []
    length = len(nodes)
    if (length % 26) != 0:
        return n
    for i in range(0, length, 26):
        nid = nodes[i:i+20]    
        ip = inet_ntoa(nodes[i+20:i+24])
        port = unpack('!H', nodes[i+24:i+26])[0]
        n.append((nid, ip, port))
    return n

def get_log2(num):
    for count in range(0, len(num)):
        i = ord(num[count])
        if i == 0:
            continue
        t = int(math.log(i, 2)) + 8 * (len(num)-count-1);
#        print(i, math.log(i, 2,), len(num), count)
        return t

def get_distance(aid, bid):
    ans = ''
    for i in range(0, IDLEN):
        ans = ans + chr(ord(aid[i]) ^ ord(bid[i])) 
    return ans
        

class KNode:
    def __init__(self, nid, ip, port):
        self.nid = nid
        self.ip = ip
        self.port = port

class Nodes:
    mutex = threading.Lock()
    def __init__(self, nid, k_size=8):
        self.k_size = k_size
        self.numbers_of_buckets = 160
        self.nid = nid
        self.buckets = [deque(maxlen=self.k_size) for _ in range(self.numbers_of_buckets)]

    def store(self, n):
        if self.nid == n.nid:
            return
        distance = get_distance(self.nid, n.nid)
        bid = get_log2(distance)
        if self.mutex.acquire(1):
            if n in self.buckets[bid]:
                self.buckets[bid].remove(n)
            self.buckets[bid].appendleft(n)
            self.mutex.release()
        #if(DEBUG): print("bid: ", bid, "ip:", n.ip, n.port)

    def find_closest(self, target):
        if self.nid == target:
            return []
        distance = get_distance(self.nid, target)
        bid = get_log2(distance)
        res = []
        while len(self.buckets[bid]) == 0:
            bid = bid - 1
        if self.mutex.acquire(1):
            for node in self.buckets[bid]:
                res.append(node)
            self.mutex.release()
        if len(res) > 3:
            return res[0:3]
        return res

if __name__ == '__main__':
    a = b'r\xbc^\x85k\xce\xd3\xe9\'\x19\xb3Ce\xbc\xf4Bf\x01\x87Z_\x8c\xd1\xf8/\xcbs\x9d$C\xfe\x89\xa91M\x91\xec\x98\xcaF\x87\xd6+\x16\x86\x99Y\xd7f\xb2z\xb6p\x97\xcdI=\x05\xf3\xca\x0e\xd7\xf2\xb1\xf4\x98\x8ft\x18"O\n\x97\xed2G\xb6Dq\x9fe\xec\x0b\xf3\x9f\xe3\xf2"\xae&\x17%\x8b\x18\xe6\x0c\x1a\x84.7\xbd sZv\xd2\x8aI\xf1\xf1\xbb\xe9\xeb\xb3\xa6\xdb<\x87\x0c>\x99$^RY\xfd\x845J2w(\xde\xd6\xaeR\x90I\xf1\xf1\xbb\xe9\xeb\xb3\xa6\xdb<\x87\x0c\xe1R\x92\x03l\x86\xcct9\t\xd9@\xa7\xd1\xa6\xdc\nD\xba\x98-\x12\xe7\x8e\x12Gq%\x8f\xc6\x03\xc6\x9eu\x1b\xfe\x89\xbdx\x96\x8f\x94\xae\xa0\x81\x93\x95\t.\xc9\xe8\x11\xc4\\\xf7;\xf64\x90'
    m = decode_nodes(a)
    print("after decoded ", m)
    print(m)
    n = encode_nodes(m)
    print("after encoded ", n)
    print(get_log2(m[0][0]))
    print(repr(get_distance(m[0][0], m[0][0])))
