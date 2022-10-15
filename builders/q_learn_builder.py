import math
from random import randint, random
from typing import Dict, List, Set, Optional

from tqdm import tqdm

from builders import MazeBuilder
from tiles.tile import Coords
from utils.graph_algorithms import Node


class QState:
    def __init__(self, state: Coords, q_actions: Dict[Coords, float]):
        """
        Represents a state with actions and their respective rewards.

        Args:
            state: Coordinates of the state/Node
            q_actions: a dictionary of the state's actions and their rewards
        """
        self.state = state
        self.q_actions = q_actions
        self.actions = set(q_actions)

    def __hash__(self):
        return hash(self.state)

    def __repr__(self):
        return f'<QState at {self.state} with QActions {self.q_actions}'


class QLearnBuilder(MazeBuilder):
    def __init__(self, coordinated_nodes: Dict[Coords, Node], tower_limit: Optional[int] = None):
        """
        Tries to find the optimal maze by finding the longest path with Q-Learning.

        Note: Optimality not guaranteed. Only works when the map has a single
        spawn, and there is no tower limit.

        Args:
            coordinated_nodes: the (Coords and) Nodes of the maze
            tower_limit: maximum number of towers allowed in the maze
        """
        super().__init__(coordinated_nodes, tower_limit)

        self.alpha = 0.5
        self.epsilon = 0.4
        training_multiplier = 3000
        self.training_times = len(self.coordinated_traversables) * training_multiplier
        self.reward_normal = 2  # Surviving
        self.reward_fail = -1   # Dead end
        self.reward_goal = 0    # Finishing
        self.goal_coords = self.get_goal_coords()

        # {state: {action: reward of action}}
        self.q: Dict[Coords, QState] = self.build_q_table()
        self.blocked: Set[Coords] = set()

    def get_goal_coords(self) -> Set[Coords]:
        """
        Obtain the goal nodes of the map.

        The neighbors of exits work as the goals, as the trainable agent has
        to move to the exit node when next to it.

        Returns:
            a set of Coordinates which end a training scenario when the agent
            lands on one of them
        """
        goal_coords = set()

        for node in self.exit_nodes:
            for neighbor in node.neighbors:
                if not neighbor.ttype.is_traversable:
                    continue
                goal_coords.add(neighbor.coords)

        return goal_coords

    def build_q_table(self) -> Dict[Coords, QState]:
        """
        Create and fill a Q-Table with default rewards.

        Returns:
            a dictionary of Coordinates connecting to the respective QStates
        """
        table = dict()

        for coords, node in self.coordinated_traversables.items():

            # Ignore exits
            if node.ttype.is_exit:
                continue

            q_actions = dict()
            for neighbor in node.neighbors:

                if not neighbor.ttype.is_traversable:
                    continue

                n_coords = neighbor.coords
                if n_coords in self.goal_coords:
                    q_actions[n_coords] = self.reward_goal

                else:
                    q_actions[n_coords] = self.reward_normal

            table[coords] = QState(coords, q_actions)

        return table

    def update(self, old_state: Coords, action: Coords, reward: float) -> None:
        """
        Update the reward of the given Q-Action in the Q-table.

        Args:
            old_state: the Coordinates of where the agent was
            action: the Coordinates where the agent moved
            reward: a float representing the action's quality
        """
        old_q_value = self.q[old_state].q_actions[action]
        best_future = self.best_possible_reward(action)
        if best_future == -math.inf:
            best_future = self.reward_fail
        delta = self.alpha * (reward + best_future - old_q_value)
        self.q[old_state].q_actions[action] = old_q_value + delta

    def best_possible_reward(self, state: Coords) -> float:
        """
        Find the largest reward of the currently possible actions from the
        given state.

        Args:
            state: the Coordinates of a QState whose possible actions to consider

        Returns:
            the largest available float reward
        """
        _, best_reward = self.get_best_available_q_action(state)
        return best_reward

    def choose_action(self, state: Coords, allow_random=True) -> Coords:
        """
        Choose a possible action from the given state. Best available
        action is chosen if random actions are not allowed or with an
        arbitrary chance.

        Args:
            state: the Coordinates of a state whose actions to consider
            allow_random: boolean for allowing random actions

        Returns:
            the Coordinates of the best or random available action
        """
        chance = random()

        if not allow_random or self.epsilon < chance:
            best_action, _ = self.get_best_available_q_action(state)
            return best_action

        else:
            # Take a random action
            actions = self.available_actions(state)
            random_index = randint(0, len(actions) - 1)
            return list(actions)[random_index]

    def available_actions(self, state: Coords) -> Set[Coords]:
        """
        Get a set of available actions, i.e. actions that are not blocked
        by previous moves.

        Args:
            state: the Coordinates of a state whose actions to consider

        Returns:
            a set of available actions
        """
        return self.q[state].actions - self.blocked

    def get_best_available_q_action(self, state: Coords) -> (Optional[Coords], float):
        """
        Get the action (and its reward) with the highest reward from
        all the available actions.

        Args:
            state: the Coordinates of a state whose actions to consider

        Returns:
            the Coordinates of the best action from the state and its reward,
            or None and -infinity if no available actions exist
        """
        actions = self.available_actions(state)
        largest = -math.inf
        best_action = None
        for k, v in self.q[state].q_actions.items():
            if k not in actions:
                continue
            if v > largest:
                largest = v
                best_action = k

        return best_action, largest

    def move(self, state: Coords, action: Coords) -> None:
        """
        Move the agent, making changes to the training scenario's actions.

        Args:
            state: the agent's current position
            action: the agent's next position
        """
        discarded = self.q[state].actions.union({state}) - {action}
        self.blocked.update(discarded)

    def train_agent(self) -> None:
        """
        Train the agent, ideally optimizing the Q-Table to have high values
        for actions that keep the agent away from goals and dead ends.
        """
        print('Training ...')
        spawn_coords = self.spawn_nodes[0].coords
        for idx in tqdm(range(self.training_times), unit=' epoch'):
            self.blocked.clear()

            current_state = spawn_coords
            while True:
                action = self.choose_action(state=current_state, allow_random=True)
                self.move(state=current_state, action=action)

                # Hit a goal Node, end scenario
                if action in self.goal_coords:
                    self.update(old_state=current_state, action=action,
                                reward=self.reward_goal)
                    break

                # No actions available, end scenario
                neighbor_actions = self.q[action].actions
                if len(neighbor_actions - self.blocked) == 0:
                    self.update(old_state=current_state, action=action,
                                reward=self.reward_fail)
                    break

                # Possible moves to be made, continue scenario
                self.update(old_state=current_state, action=action,
                            reward=self.reward_normal)

                current_state = action

    def get_path(self) -> Optional[Set[Coords]]:
        """
        Get the path that a trained agent takes on the map.

        Returns:
            a set of Coordinates that the agent takes on the map, or None if
            the agents ends up in an dead end
        """
        spawn_coords = self.spawn_nodes[0].coords
        path_taken = set()

        self.blocked.clear()

        current_state = spawn_coords
        while True:
            action = self.choose_action(state=current_state, allow_random=False)
            self.move(state=current_state, action=action)
            path_taken.add(action)

            # Hit a goal Node, end scenario
            if action in self.goal_coords:
                break

            # No actions available, end scenario unsuccessfully
            neighbor_actions = self.q[action].actions
            if len(neighbor_actions - self.blocked) == 0:
                return None

            current_state = action

        return path_taken

    def generate_optimal_mazes(self) -> List[List[Coords]]:
        """
        Train an agent on the map, which tries to find the longest path with
        constraints. Towers are placed around the path, blocking anyone
        from straying off the path.

        Returns:
            a list of lists with Coordinates for the (ideally) optimal tower
            placements, or an empty list of lists if the agent ends up in a
            dead end, even after all it has learned.
        """
        self.train_agent()
        path = self.get_path()
        if not path:
            return [[]]
        self.best_tower_coords = [coords
                                  for coords in self.coordinated_build_nodes
                                  if coords not in path]
        # todo only include tower coords that block something
        return [self.best_tower_coords]


