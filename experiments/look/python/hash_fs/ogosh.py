import networkx as nx
from hashlib import sha256
from typing import Any


class Node:
    def __init__(self, data=b""):
        self._data: Any = data
        self.hid = self.__hash__()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self.hid = self.__hash__()

    def __hash__(self) -> bytes:
        sha = sha256(self._data).hexdigest().encode()
        return sha

    def __repr__(self):
        return f"N({self.data})"


class HashTree:
    def __init__(self, root: Node):
        self.graph = nx.DiGraph()
        self.graph.add_node(root.hid, node=root)
        self.root = root

    def append_to(self, parent: Node, child: Node):
        if child.hid not in self.graph:
            self.graph.add_node(child.hid, node=child)
        self.graph.add_edge(parent.hid, child.hid)
        child.hid = child.__hash__()

    def ancestors(self, node: Node):
        return nx.ancestors(self.graph, node.hid)

    def invalidate_ancestry(self, node: Node):
        for ancestor_hid in self.ancestors(node):
            ancestor_node = self.graph.nodes[ancestor_hid]["node"]
            ancestor_node.hid = None

    def update_ancestry(self, node: Node):
        node.hid = node.__hash__()
        for ancestor_hid in self.ancestors(node):
            ancestor_node = self.graph.nodes[ancestor_hid]["node"]
            ancestor_node.hid = ancestor_node.__hash__()

    @property
    def invalid_nodes(self):
        return [
            hid
            for hid, data in self.graph.nodes.data()
            if hid != data["node"].__hash__()
        ]


def main():
    R = Node()
    T = HashTree(R)

    A = Node(b"Hello")
    B = Node(b"World")
    C = Node(b"!")

    D = Node(b"Ox")
    E = Node(b"and")
    F = Node(b"Fox")
    G = Node(b"!")
    H = Node(b"!!")

    T.append_to(R, A)
    T.append_to(A, B)
    T.append_to(B, C)

    T.append_to(R, D)
    T.append_to(D, E)
    T.append_to(D, F)
    T.append_to(F, G)
    T.append_to(F, H)

    # T.invalidate_ancestry(F)
    # Now you can use any networkx functions on T.graph as required.
    print(T.invalid_nodes)


if __name__ == "__main__":
    main()
