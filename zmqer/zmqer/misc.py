from itertools import combinations
from random import random


def connect_all(peers):
    for p, p2 in combinations(peers, 2):
        p.join_group(p2.address)
        p2.join_group(p.address)


def connect_linked(peers):
    for p, p2 in zip(peers, peers[1:]):
        p.join_group(p2.address)

    peers[-1].join_group(peers[0].address)


def connect_random(peers):
    for p, p2 in combinations(peers, 2):
        if random() < 0.5:
            p.join_group(p2.address)
            p2.join_group(p.address)
