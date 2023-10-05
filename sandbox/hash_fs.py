from dataclasses import Field, dataclass
import glob
from hashlib import sha256
from uuid import uuid4


class Node:
    def __init__(self, data=b"", children=None):
        self._data = data
        self._parent = None
        self._children = children or []

        self._hid = self.__calculate_hash()

    @property
    def hid(self):
        return self._hid

    @hid.setter
    def set_hid(self, hid):
        self._hid = hid

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self.__update_node_hashes(self)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent
        self.__update_node_hashes(self)

    @property
    def children(self):
        return self._children

    def __calculate_hash(self):
        if len(self._children) == 0:
            return sha256(self._data).hexdigest()
        else:
            return sha256(b"".join([child.hid for child in self._children])).hexdigest()

    def __get_path_to_root(self, node: "Node"):
        """Get the path from node to root. Assumes that node is in the tree."""
        path = []
        while node:
            path.append(node)
            node = node._parent
        return path

    def __update_node_hashes(self, changed_node: "Node"):
        """Update hashes of all nodes in the path from changed_node to root"""
        for node in self.__get_path_to_root(changed_node):
            node.set_hid(node.__calculate_hash())

    def __str__(self):
        return self.hid

    def __repr__(self):
        return self.hid


class HashTree:
    """A  hash tree for file system.

    Every node is a hash value of its children.
    """

    def __init__(self, root: Node):
        self.root = root

    def append_to(self, parent: Node, child: Node):
        """Append child to parent"""
        parent._children.append(child)
        child._parent = parent


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

    T.append_to(R, D)
    T.append_to(D, E)
    T.append_to(D, F)
    T.append_to(F, G)
    T.append_to(F, H)

    print(T.root)


if __name__ == "__main__":
    main()
