from queue import Queue
from typing import Tuple, Dict, NamedTuple

import numpy as np

from utils.tile import Coords, Tile

NEIGHBOR_DELTAS = [(0, 1), (-1, 0), (1, 0), (0, -1)]


class Node:
    def __init__(self, coords: Coords, ttype: str):
        """
        A node used in a graph.

        Args:
            coords: coordinates (Coords) of the node in a built map
            ttype: tile type that the node is based on
        """
        self._coords = coords
        self._ttype = ttype
        self._visited = False
        self._distance = 0
        self._prequel = None
        self.neighbors = set()

    @property
    def coords(self) -> Coords:
        return self._coords

    @coords.setter
    def coords(self, coords: Coords) -> None:
        self._coords = coords

    @property
    def ttype(self) -> str:
        return self._ttype

    @ttype.setter
    def ttype(self, ttype: str) -> None:
        self._ttype = ttype

    @property
    def visited(self) -> bool:
        return self._visited

    @visited.setter
    def visited(self, is_visited: bool) -> None:
        self._visited = is_visited

    @property
    def distance(self) -> int:
        return self._distance

    @distance.setter
    def distance(self, dist: int) -> None:
        self._distance = dist

    @property
    def prequel(self) -> "Node":
        return self._prequel

    @prequel.setter
    def prequel(self, preq: "Node") -> None:
        self._prequel = preq

    def connect_undirected(self, node: "Node") -> None:
        self.neighbors.add(node)
        node.neighbors.add(self)

    def remove_undirected(self, node: "Node") -> None:
        self.neighbors.discard(node)
        node.neighbors.discard(self)

    def connect_directed(self, node: "Node") -> None:
        self.neighbors.add(node)

    def remove_directed(self, node: "Node") -> None:
        self.neighbors.discard(node)


def tiles_to_nodes(tiles: np.ndarray) -> Dict[Coords, Node]:
    """
    Create Node objects from Tiles.

    Args:
        tiles: an array of Tiles

    Returns:
        a dictionary with coordinates as keys and Nodes as values
    """
    nodes = {}
    for tile in tiles:
        coords = tile.coords
        node = Node(coords, tile.tile_type)
        nodes[coords] = node

    return nodes


def connect_all_neighboring_nodes(nodes: Dict[Coords, Node]) -> None:
    """
    Connect all the given Nodes together, so that a single Node is
    connected to its 4 possible neighbors.

    Args:
        nodes: a dictionary with the connectable Nodes as values
    """
    for coords, node in nodes.items():

        for coords2 in [Coords(*tuple(map(sum, zip(coords, delta)))) for delta in NEIGHBOR_DELTAS]:
            if coords2 in nodes.keys():
                node.connect_directed(nodes[coords2])


def reset_nodes(nodes: Dict[Coords, Node]) -> None:
    """
    Reset all given Nodes.

    Args:
        nodes: a dictionary with the resetable Nodes as values
    """
    for node in nodes.values():
        reset_node(node)


def reset_node(node: Node) -> None:
    """
    Reset a single Node's data, while not reseting the neighbors.

    Args:
        node: a Node to be reset
    """
    node.visited = False
    node.distance = 0
    node.prequel = 0


def reset_node_fully(node: Node) -> None:
    """
    Reset a single Node's data, including the reference of neighbors.

    Args:
        node: a Node to be reset
    """
    reset_node(node)
    node.neighbors = set()


def depth_first_search_any_ttype(node, ending_ttype: str) -> Node:
    """
    Using a recursive DFS, find any Node with the given tile type.
    Args:
        node: starting/current Node
        ending_ttype: the tile type to be found

    Returns:
        a Node with the given tile type, or None if none is connected
    """
    node.visited = True

    for neighbor in node.neighbors:

        if not neighbor.visited:

            if neighbor.ttype == ending_ttype:
                return neighbor
            ending_node = depth_first_search_any_ttype(neighbor, ending_ttype)
            if ending_node:
                return ending_node


def breadth_first_search(starting_node: Node, ending_type: str, node_count: int) -> Node:
    """
    Unused BFS

    Args:
        starting_node:
        ending_type:
        node_count:

    Returns:

    """
    starting_node.visited = True
    starting_node.distance = 0
    queue = Queue(maxsize=node_count-1)
    queue.put(starting_node)
    while not queue.empty():
        node = queue.get()
        for neighbor in node.neighbors:
            if not neighbor.visited:
                if neighbor.ttype == ending_type:
                    return neighbor
                neighbor.visited = True
                neighbor.distance = node.distance + 1
                neighbor.parent = node
                queue.put(neighbor)

