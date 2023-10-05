from dataclasses import Field, dataclass
import glob
from hashlib import sha256
from typing import Any
from uuid import uuid4


class Node:
    def __init__(self, data=b"", children=None):
        self._hid: bytes = None
        self._parent: "Node" = None
        self._children: list["Node"] = children or []
        self._data: Any = data

        self.update()

    @property
    def hid(self):
        if not self._hid:
            self._hid = self.__hash__()
        return self._hid

    @hid.setter
    def hid(self, hid):
        self._hid = hid

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent
        self.update()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self.update()

    @property
    def children(self):
        return self._children

    def add_child(self, child: "Node"):
        self._children.append(child)
        child.parent = self

    def __hash__(self) -> bytes:
        sha = sha256(self._data).hexdigest().encode()
        if len(self.children) == 0:
            return sha
        else:
            shas = [sha] + [child.hid for child in self.children]
            return sha256(b"".join(shas)).hexdigest().encode()

    def get_root_path(self, node: "Node"):
        """Get the path from node to root. Assumes that node is in the tree."""
        while node:
            yield node
            node = node.parent

    def update(self, changed_node: "Node" = None):
        """Update hashes of all nodes in the path from changed_node to root"""
        changed_node = changed_node or self
        for node in self.get_root_path(changed_node):
            node.hid = node.__hash__()

    def __str__(self):
        return f"{self.hid}: {self.data}"

    def __repr__(self):
        return f"N({self.data})"


class HashTree:
    """A  hash tree for file system.

    Every node is a hash value of its children.
    """

    def __init__(self, root: Node):
        self.root = root
        self.nodes = [root]
        self.cache = {}
        self.cache_histories = []

    def append_to(self, parent: Node, child: Node):
        """Append child to parent"""
        parent.add_child(child)
        self.nodes.append(child)

    def initialize_cache(self):
        """Generate cache for the tree to check against invalidation"""
        self.cache = {node.hid: node for node in self.nodes}

    @property
    def invalid_nodes(self):
        """Return invalidated nodes or empty list if no nodes are invalidated"""
        return [
            node
            for node in self.nodes
            if node.hid not in self.cache or node.hid != self.cache[node.hid].hid
        ]

    def invalidate_ancestry(self, node: Node):
        """Invalidate ancestry of node"""
        for ancestor in node.get_root_path(node):
            if ancestor.hid in self.cache:
                del self.cache[ancestor.hid]

    def update_ancestry(self, node: Node):
        """Update node and its ancestry"""
        node.update()
        self.cache[node.hid] = node
        for ancestor in node.get_root_path(node):
            self.cache[ancestor.hid] = ancestor


class FSIndex:
    """Index for file system"""

    ...


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
    print(T.invalid_nodes)
    T.initialize_cache()
    print(T.invalid_nodes)

    T.append_to(R, D)
    T.append_to(D, E)
    T.append_to(D, F)
    T.append_to(F, G)
    T.append_to(F, H)
    print(T.invalid_nodes)
    T.update_ancestry(F)
    print(T.invalid_nodes)


if __name__ == "__main__":
    main()
