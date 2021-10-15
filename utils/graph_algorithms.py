from queue import Queue
from typing import Dict, Type, Set, List, Optional

import numpy as np

from tiles.tile import Coords
from tiles.tile_type import TType

NEIGHBOR_DELTAS = {
    4: [(0, 1), (-1, 0), (1, 0), (0, -1)],
    8: [(-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (0, -1), (1, -1)]
}


class Node:
    def __init__(self, coords: Coords, ttype: Type[TType]):
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
        self.neighbors: Set["Node"] = set()

    @property
    def coords(self) -> Coords:
        return self._coords

    @coords.setter
    def coords(self, coords: Coords) -> None:
        self._coords = coords

    @property
    def ttype(self) -> Type[TType]:
        return self._ttype

    @ttype.setter
    def ttype(self, ttype: Type[TType]) -> None:
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

    def remove_all_undirected(self) -> None:
        for neighbor in self.neighbors:
            neighbor.remove_directed(self)
        self.neighbors = set()


class Distances:
    def __init__(self):
        """
        Holds a list of distances between Nodes. Two instances are compared
        in an ascending order.
        """
        self.dists = []

    def append(self, item: int) -> None:
        self.dists.append(item)

    def sort(self) -> None:
        self.dists.sort()

    def __gt__(self, other: "Distances") -> bool:
        self.sort()
        other.sort()
        return self.dists > other.dists

    def __ge__(self, other: "Distances") -> bool:
        self.sort()
        other.sort()
        return self.dists >= other.dists

    def __eq__(self, other: "Distances") -> bool:
        self.sort()
        other.sort()
        return self.dists == other.dists


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
        node = Node(coords, tile.ttype)
        nodes[coords] = node

    return nodes


def connect_all_neighboring_nodes(nodes: Dict[Coords, Node], neighbor_count: int) -> None:
    """
    Connect all the given Nodes together, so that a single Node is
    connected to its 4 or 8 possible neighbors.

    Args:
        nodes: a dictionary with the connectable Nodes as values
        neighbor_count: the number of neighbors a Node can have
    """
    deltas = NEIGHBOR_DELTAS[neighbor_count]
    for coords, node in nodes.items():

        for coords2 in [Coords(*tuple(map(sum, zip(coords, delta)))) for delta in deltas]:
            if coords2 in nodes.keys():
                node.connect_directed(nodes[coords2])


def reset_nodes(nodes: List[Node]) -> None:
    """
    Reset all given Nodes.

    Args:
        nodes: a list of resetable Nodes
    """
    for node in nodes:
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


def unvisit_nodes(nodes: List[Node]) -> None:
    for node in nodes:
        node.visited = False


def reset_node_fully(node: Node) -> None:
    """
    Reset a single Node's data, including the reference of neighbors.

    Args:
        node: a Node to be reset
    """
    reset_node(node)
    node.neighbors = set()


def depth_first_search_any_ttype(node, ending_ttype: Type[TType]) -> Node:
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

        if not neighbor.visited and neighbor.ttype.is_traversable:

            if neighbor.ttype == ending_ttype:
                return neighbor
            ending_node = depth_first_search_any_ttype(neighbor, ending_ttype)
            if ending_node:
                return ending_node


def get_shortest_distance_any(starting_node: Node, ending_type: Type[TType],
                              node_count: int) -> Optional[int]:
    """
    Calculate and return the distance between a Node and any other Node
    corresponding to the given type.

    Args:
        starting_node: a starting Node for the graph algorithm
        ending_type: the tile type to be found
        node_count: maximum number of Nodes in a Queue

    Returns:
        the distance between the given node and any Node of the given type,
        or None if a route is not available
    """
    starting_node.visited = True
    starting_node.distance = 0
    queue = Queue(maxsize=node_count-1)
    queue.put(starting_node)
    while not queue.empty():
        node = queue.get()
        for neighbor in node.neighbors:
            if not neighbor.visited and neighbor.ttype.is_traversable:
                if neighbor.ttype == ending_type:
                    return node.distance + 1
                neighbor.visited = True
                neighbor.distance = node.distance + 1
                neighbor.parent = node
                queue.put(neighbor)


def get_closest_any(starting_node: Node, ending_type: Type[TType],
                    node_count: int) -> Optional[Node]:
    """
    Find a Node of the given type that is closest to the starting Node.

    Args:
        starting_node: a starting Node for the graph algorithm
        ending_type: the tile type to be found
        node_count: maximum number of Nodes in a Queue

    Returns:
        the closest Node corresponding to the given tile type from the starting
        Node, or None if no route is available
    """
    starting_node.visited = True
    starting_node.distance = 0
    queue = Queue(maxsize=node_count-1)
    queue.put(starting_node)
    while not queue.empty():
        node = queue.get()
        for neighbor in node.neighbors:
            if not neighbor.visited and neighbor.ttype.is_traversable:
                neighbor.visited = True
                neighbor.distance = node.distance + 1
                neighbor.parent = node

                if neighbor.ttype == ending_type:
                    return neighbor
                queue.put(neighbor)


def get_distances(starting_nodes: List[Node], ending_type: Type[TType],
                  current_nodes: List[Node]) -> Optional[Distances]:
    """
    Calculate and return the distances between starting Nodes and their
    closest Nodes with the corresponding tile type.

    Args:
        starting_nodes: a list of starting Nodes
        ending_type: a tile type to count the distances to
        current_nodes: a list of Nodes currently in the graph which are
                       needed for resetting

    Returns:
        a Distances object with distances of each starting Node, or None
        if even a single route is unavailable
    """
    dists = Distances()
    node_count = len(current_nodes)
    for start_node in starting_nodes:
        unvisit_nodes(current_nodes)
        dist = get_shortest_distance_any(start_node, ending_type,
                                         node_count)
        if not dist:
            return None
        dists.append(dist)
    return dists


def get_maxmin_distance(starting_nodes: List[Node], ending_type: Type[TType],
                        current_nodes: List[Node]) -> Optional[int]:
    """
    Calculate and return the maxmin distance of a map. The value returned
    is the greatest shortest distance between different spawn nodes.

    Args:
        starting_nodes: a list of starting Nodes
        ending_type: a tile type to count the distance to
        current_nodes: a list of Nodes currently in the graph which are
                       needed for resetting
    Returns:
        the maxmin distance between the starting Nodes and Nodes corresponding
        to the given tile type, or None if no route is available
    """
    maxmin_distance = None
    node_count = len(current_nodes)
    for start_node in starting_nodes:
        unvisit_nodes(current_nodes)
        dist = get_shortest_distance_any(start_node, ending_type,
                                         node_count)
        if not maxmin_distance or (dist and dist > maxmin_distance):
            maxmin_distance = dist

    return maxmin_distance


def get_cluster_of_nodes(current_node: Node) -> List[Node]:
    """
    Recursively find a cluster of nodes that share the same node type. A cluster
    contains one or more nodes where they are all connected via neighbors.

    Args:
        current_node: the current node whose neighbors are checked

    Returns:
        a list of connected nodes, sharing the same tile type
    """
    cluster = []
    current_node.visited = True
    cluster.append(current_node)
    node_type = current_node.ttype
    for neighbor in current_node.neighbors:
        if neighbor.ttype == node_type and not neighbor.visited:
            cluster += get_cluster_of_nodes(neighbor)

    return cluster
