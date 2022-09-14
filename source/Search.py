import Helper as He
import random as rd
from queue import PriorityQueue

def Apply(rule, x, y, state, MX):
    for dy in range(rule.OMY):
        for dx in range(rule.OMX):
            state[x + dx + (y + dy) * MX] = rule.output[dx + dy * rule.OMX]


def Applys(state, solution, MX):
    result = [0 for i in range(len(state))]
    result = state[:len(state)]
    for (rule, i) in solution:
        Apply(rule, int(i % MX), int(i / MX), result, MX)
    return result

def Applied(rule, x, y, state, MX):
    result = [0 for i in range(len(state))]
    result = state
    for dz in range(rule.OMZ):
        for dy in range(rule.OMY):
            for dx in range(rule.OMX):
                newvalue = rule.output[dx + dy * rule.OMX + dz * rule.OMX * rule.OMY]
                if newvalue != 0xff:
                    result[x + dx + (y + dy) * MX] = newvalue
    return result


def Print(state, MX, MY):
    characters = ['.', 'R', 'W', '#', 'a', '!', '?', '%', '0', '1', '2', '3', '4', '5']
    for y in range(MY):
        for x in range(MX):
            print("{0}[{1}[{2}]]".format(characters, state, x + y * MX))
        print("\n")


def Matches(rule, x, y, state, MX, MY):
    if x + rule.IMX > MX or y + rule.IMY > MY:
        return False
    dy = dx = 0
    for di in range(len(rule.input)):
        if (rule.input[di] & (1 << state[x + dx + (y + dy) * MX]) == 0):
            return False
        dx += 1
        if dx == rule.IMX:
            dx = 0
            dy += 1
    return True


def IsInside(p, rule, x, y):
    return x <= p[0] and p[0] < x + rule.IMX and y <= p[1] and p[1] < y + rule.IMY


def Overlap(rule0, x0, y0, rule1, x1, y1):
    for dy in range(rule0.IMY):
        for dx in range(rule1.IMX):
            if IsInside((x0 + dx, y0 + dy), rule1, x1, y1):
                return True
    return False


def Hide(l, unhide, tiles, amounts, mask, MX):
    mask[l] = unhide
    (rule, i) = tiles[l]
    x = int(i % MX)
    y = int(i / MX)
    incr = 1 if unhide else -1
    for dy in range(rule.IMY):
        for dx in range(rule.IMX):
            amounts[x + dx + (y + dy) * MX] += incr


def Enumerate(children, solution, tiles, amounts, mask, state, MX):
    I = He.MaxPositiveIndex(amounts)
    X = int(I % MX)
    Y = int(I / MX)
    if I < 0:
        children.append(Applys(state, solution, MX))
        return
    cover = []
    for l in range(len(tiles)):
        (rule, i) = tiles[l]
        if mask[l] and IsInside((X, Y), rule, int(i % MX), int(i / MX)):
            cover.append((rule, i))

    for (rule, i) in cover:
        solution.append((rule, i))
        intersecting = []
        for l in range(len(tiles)):
            if mask[l]:
                (rule1, i1) = tiles[i]
                if Overlap(rule, int(i % MX), int(i / MX), rule1, int(i1 % MX), int(i1 / MX)):
                    intersecting.append(l)
        for l in intersecting:
            Hide(l, False, tiles, amounts, mask, MX)
        Enumerate(children, solution, tiles, amounts, mask, state, MX)
        for l in intersecting:
            Hide(l, True, tiles, amounts, mask, MX)           



def AllChildStates(state, MX, MY, rules):
    list = []
    amounts = [0 for i in range(len(state))]
    for i in range(len(state)):
        x = int(i % MX)
        y = int(i / MX)
        for r in range(len(rules)):
            rule = rules[r]
            if Matches(rule, x, y, state, MX, MY):
                list.append((rule, i))
                for dy in range(rule.IMY):
                    for dx in range(rule.IMX):
                        amounts[x + dx + (y + dy) * MX] += 1
    tiles = list
    mask = [True for i in range(len(tiles))]
    solution = []
    result = []
    Enumerate(result, solution, tiles, amounts, mask, state, MX)
    return result


def OneChildStates(state, MX, MY, rules):
    result = []
    for rule in rules:
        for y in range(MY):
            for x in range(MX):
                if Matches(rule, x, y, state, MX, MY):
                    result.append(Applied(rule, x ,y, state, MX))

    return result


def Run(present, future, rules, MX, MY, MZ, C, all, limit, depth_coefficient, seed):
    import Observation
    bpotentials = [[-1 for i in range(len(present))] for i in range(C)]
    fpotentials = [[-1 for i in range(len(present))] for i in range(C)]

    Observation.Observation.ComputeBackwardPotentials(bpotentials, future, MX, MY, MZ, rules)
    root_backward_estimate = Observation.Observation.BackwardPointwise(bpotentials, present)
    Observation.Observation.ComputeForwardPotentials(fpotentials, present, MX, MY, MZ, rules)
    root_forward_estimate = Observation.Observation.ForwardPointwise(fpotentials, future)

    if root_backward_estimate < 0 or root_forward_estimate < 0:
        print("INCORRECT PROBLEM")
        return None

    print("root estimate = ({0}, {1})".format(root_backward_estimate, root_forward_estimate))
    if root_backward_estimate == 0:
        return [[]]

    root_board = Board(present, -1, 0, root_backward_estimate, root_forward_estimate)

    database = []
    database.append(root_board)
    visited = {}
    visited[present] = 0

    frontier = PriorityQueue()
    frontier.put((0, root_board.Rank(seed, depth_coefficient)))
    frontier_length = 1

    record = root_backward_estimate + root_forward_estimate
    while frontier_length > 0 and (limit < 0 or len(database) < limit):
        parent_index = frontier.get()
        frontier_length -= 1
        parent_board = database[parent_index]

        children = AllChildStates(parent_board.state, MX, MY, rules) if all else OneChildStates(parent_board.state, MX, MY, rules)

        for child_state in children:
            child_index = 0
            if child_state in visited.keys():
                child_index = visited[child_state]
                old_board = database[child_index]
                if parent_board.depth + 1 < old_board.depth:
                    old_board.depth = parent_board.depth + 1
                    old_board.parent_index = parent_index
                    if old_board.backward_estimate >= 0 and old_board.forward_estimate >= 0:
                        frontier.put((child_index, old_board.Rank(seed, depth_coefficient)))
                        frontier_length += 1
            else:
                child_backward_estimate = Observation.Observation.BackwardPointwise(bpotentials, child_state)
                Observation.Observation.ComputeForwardPotentials(fpotentials, child_state, MX, MY, MZ, rules)
                child_forward_estimate = Observation.Observation.ForwardPointwise(fpotentials, future)

                if child_backward_estimate < 0 or child_forward_estimate < 0:
                    continue
                child_borad = Board(child_state, parent_index, parent_board.depth + 1, child_backward_estimate, child_forward_estimate)
                database.append(child_borad)
                child_index = len(database) - 1
                visited[child_borad.state, child_index]

                if child_borad.forward_estimate == 0:
                    print("found a trajectory of length {0}, visited {1} states".format(parent_board.depth + 1, len(visited)))
                    trajectory = Board.Trajectory(child_index, database)
                    trajectory.reverse()
                    return list(map(lambda x : x.state, trajectory))
                else:
                    if limit < 0 and child_backward_estimate + child_forward_estimate <= record:
                        record = child_backward_estimate + child_forward_estimate
                        print("found a state of record extimate {0} = {1} + {2}".format(record, child_backward_estimate, child_forward_estimate))
                        Print(child_state, MX, MY)
                    frontier.put((child_index, child_borad.Rank(seed, depth_coefficient)))
                    frontier_length += 1

    return None


class Board():
    def __init__(self, state, parent_index, depth, backward_estimate, forward_estimate):
        self.state = state
        self.parent_index = parent_index
        self.depth = depth
        self.backward_estimate = backward_estimate
        self.forward_estimate = forward_estimate

    def Rank(self, random, depth_coefficient):
        result = 1000 - self.depth if depth_coefficient else self.forward_estimate + self.backward_estimate + 2.0 * depth_coefficient * self.depth
        
        return result + 0.0001 * rd.uniform(0,1)

    @staticmethod
    def Trajectory(index, database):
        result = []
        board = database[index]
        while board.parent_index >= 0:
            result.append(board)
            board = database[board.parent_index]
        return result
