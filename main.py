import heapq
import os
import time
from abc import ABC
from collections.abc import Sized

# Flags that can be changed to change which optimizations are in place
should_initialize_constraints = True
forwardChecking = True
lrv = True


class Board:
    def __init__(self, board):
        self.board = board
        self.rows = len(board)
        self.columns = len(board[0])

    def __str__(self):
        total = ""
        total += "╋━━━━━" * (len(self.board[0])) + "╋\n"
        for row in self.board:
            total += "┃"
            for tile in row:
                if isinstance(tile, Slot):
                    total += "  " + str(tile.value) + "  "
                elif isinstance(tile, Wall):
                    total += (("" if not tile.verticalSum else str(tile.verticalSum)).rjust(2, "█") +
                              "╲" +
                              ("" if not tile.horizontalSum else str(tile.horizontalSum)).ljust(2, "█"))
                total += "┃"
            total += "\n"
            total += "╋━━━━━" * (len(row)) + "╋"
            total += "\n"
        return total

    def tileAt(self, row, column):
        return self.board[row][column]


class Slot:
    def __init__(self, value, row, col, horizontalWall, verticalWall):
        self.value = value
        self.constraints = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}
        self.row = row
        self.col = col
        self.horizontalWall = horizontalWall
        self.verticalWall = verticalWall


class Wall:
    def __init__(self, horizontalSum, verticalSum, row, col):
        self.horizontalSum = horizontalSum
        self.verticalSum = verticalSum
        self.row = row
        self.col = col
        self.horizontalGroup = []
        self.verticalGroup = []


class Statistics:
    def __init__(self):
        self.attempts = 0


class EmptySlotQueue(Sized, ABC):
    def __len__(self):
        raise Exception()

    def pop(self):
        raise Exception()

    def enqueue(self, emptySlot):
        raise Exception()

    def remove(self, emptySlotToRefresh):
        raise Exception()

    def resort(self):
        raise Exception()

    def all(self):
        raise Exception()


class EmptySlotNaiveQueue(EmptySlotQueue):
    def __init__(self, queue):
        self.queue = queue
        self.index = 0

    def __len__(self):
        return len(self.queue) - self.index

    def pop(self):
        temp = self.queue[self.index]
        self.index += 1
        return temp

    def enqueue(self, emptySlot):
        self.index -= 1

    def remove(self, emptySlotToRefresh):
        pass

    def resort(self):
        pass

    def all(self):
        return self.queue


def key(slot):
    return -len([k for (k, v) in slot.constraints.items() if v > 0]), slot.row, slot.col


class EmptySlotLRVQueue(EmptySlotQueue):
    def __init__(self, tiles):
        self.queue = [(key(tile), tile) for tile in tiles]
        heapq.heapify(self.queue)

    def __len__(self):
        return len(self.queue)

    def pop(self):
        return heapq.heappop(self.queue)[1]

    def enqueue(self, emptySlot):
        heapq.heappush(self.queue, (key(emptySlot), emptySlot))

    def remove(self, emptySlotToRefresh):
        pass

    def resort(self):
        self.queue = [(key(tile), tile) for _, tile in self.queue]
        heapq.heapify(self.queue)

    def all(self):
        return [v for (k, v) in self.queue]


def kakuro():
    board = read_input()
    print("Initial board:")
    print(board)
    statistics = Statistics()
    start_time = time.time()
    backtracking(board, statistics)
    total_time = time.time() - start_time
    print("Solved board:")
    print(board)
    print(f"Number of values attempted: {statistics.attempts}")
    print(f"Total time taken: {total_time} seconds")


def read_input():
    last_wall_in_row = []
    last_wall_in_column = []
    while True:
        filepath = input("Please input the filename: ")
        if os.path.isfile(filepath):
            break
    with open(filepath, 'r') as file:
        board = []
        for i, raw_line in enumerate(file):
            last_wall_in_row.append(None)
            raw_tiles = raw_line.split(",")
            row = []
            for j, raw_tile in enumerate(raw_tiles):
                last_wall_in_column.append(None)
                stripped = raw_tile.strip()
                if "\\" in stripped:
                    [verticalSum, horizontalSum] = stripped.split("\\")
                    wall = Wall(
                        None if horizontalSum == "" else int(horizontalSum),
                        None if verticalSum == "" else int(verticalSum),
                        i,
                        j
                    )
                    last_wall_in_row[i] = wall
                    last_wall_in_column[j] = wall
                    row.append(wall)
                else:
                    slot = Slot(0 if stripped == "" else int(stripped), i, j, last_wall_in_row[i],
                                last_wall_in_column[j])
                    row.append(slot)
                    last_wall_in_row[i].horizontalGroup.append(slot)
                    last_wall_in_column[j].verticalGroup.append(slot)
            board.append(row)
    return Board(board)


def backtracking(board: Board, statistics: Statistics):
    empty_slots = get_empty_slots(board)
    if should_initialize_constraints:
        initialize_constraints(empty_slots)
    backtracking_helper(board, empty_slots, statistics)


def initialize_constraints(emptySlots):
    for emptySlot in emptySlots.all():
        horizontalWall = emptySlot.horizontalWall
        verticalWall = emptySlot.verticalWall
        horizontalLowerBound, horizontalUpperBound = get_bounds(horizontalWall.horizontalSum,
                                                                len(horizontalWall.horizontalGroup))
        verticalLowerBound, verticalUpperBound = get_bounds(verticalWall.verticalSum,
                                                            len(verticalWall.verticalGroup))
        lowerBound = max(horizontalLowerBound, verticalLowerBound)
        upperBound = min(horizontalUpperBound, verticalUpperBound)
        for i in range(1, 9 + 1):
            if i < lowerBound or i > upperBound:
                emptySlot.constraints[i] += 1
        if len(horizontalWall.horizontalGroup) == 2 and horizontalWall.horizontalSum % 2 == 0:
            emptySlot.constraints[horizontalWall.horizontalSum // 2] += 1
        if len(verticalWall.verticalGroup) == 2 and verticalWall.verticalSum % 2 == 0:
            emptySlot.constraints[verticalWall.verticalSum // 2] += 1
    emptySlots.resort()


def get_bounds(targetSum, groupSize):
    minSumFromGroupMinusOne = sum_of_consecutive(1, groupSize - 1)
    maxSumFromGroupMinusOne = sum_of_consecutive(9 - groupSize + 2, 9)
    lowerBound = min([n for n in range(1, 9 + 1) if n + maxSumFromGroupMinusOne >= targetSum])
    upperBound = max([n for n in range(1, 9 + 1) if n + minSumFromGroupMinusOne <= targetSum])
    return (lowerBound, upperBound)


def sum_of_consecutive(low, high):
    return (high - low + 1) * (low + high) // 2

def get_empty_slots(board: Board):
    tiles = []
    for i, row in enumerate(board.board):
        for j, tile in enumerate(row):
            if isinstance(tile, Slot):
                tiles.append(tile)
    return EmptySlotLRVQueue(tiles) if lrv else EmptySlotNaiveQueue(tiles)


def backtracking_helper(board: Board, emptySlots: EmptySlotQueue, statistics: Statistics):
    if len(emptySlots) == 0:
        return True
    # print(board)
    emptySlot = emptySlots.pop()
    emptySlotTile = board.tileAt(emptySlot.row, emptySlot.col)
    availableNumbers = available_numbers(board, emptySlot.row, emptySlot.col)
    for availableNumber in availableNumbers:
        emptySlotTile.value = availableNumber
        statistics.attempts += 1
        should_undo = False
        if forwardChecking:
            should_undo = forward_checking(board, emptySlot.row, emptySlot.col, availableNumber, True)
            emptySlots.resort()
        if not should_undo and backtracking_helper(board, emptySlots, statistics):
            return True
        if forwardChecking:
            forward_checking(board, emptySlot.row, emptySlot.col, availableNumber, False)
            emptySlots.resort()
        emptySlotTile.value = 0
    emptySlots.enqueue(emptySlot)
    return False


def available_numbers(board: Board, row, column):
    horizontalAvailableNumbers = available_numbers_helper(board, row, column, True)
    verticalAvailableNumbers = available_numbers_helper(board, row, column, False)
    return set(horizontalAvailableNumbers).intersection(set(verticalAvailableNumbers))


def available_numbers_helper(board: Board, row: int, column: int, horizontal: bool):
    availableNumbers = [k for k, v in board.tileAt(row, column).constraints.items() if v == 0]
    tile = tile_at_new_row_or_column(board, row, column, row_or_column(row, column, horizontal), horizontal)
    requiredSum = tile.horizontalWall.horizontalSum if horizontal else tile.verticalWall.verticalSum
    currentSum = 0
    blankSlotsRemaining = 0
    group = tile.horizontalWall.horizontalGroup if horizontal else tile.verticalWall.verticalGroup
    for groupTile in group:
        currentSum += groupTile.value
        if groupTile.value in availableNumbers:
            availableNumbers.remove(groupTile.value)
        if groupTile.value == 0:
            blankSlotsRemaining += 1
    remainingSum = requiredSum - currentSum

    if blankSlotsRemaining == 1:
        return [number for number in availableNumbers if number == remainingSum]

    return [number for number in availableNumbers if number <= remainingSum]


def forward_checking(board: Board, row: int, column: int, value: int, add: bool):
    initial_tile = board.tileAt(row, column)
    groupTiles = [
        *initial_tile.horizontalWall.horizontalGroup,
        *initial_tile.verticalWall.verticalGroup
    ]
    for groupTile in groupTiles:
        if groupTile.value == 0:
            if add:
                groupTile.constraints[value] += 1
            else:
                groupTile.constraints[value] -= 1
    should_undo = any([all([value > 0 for value in groupTile.constraints.values()]) for groupTile in groupTiles])
    return should_undo


def row_or_column(row: int, column: int, horizontal: bool):
    return column if horizontal else row


def tile_at_new_row_or_column(board: Board, row: int, column: int, value: int, horizontal: bool):
    return board.tileAt(row, value) if horizontal else board.tileAt(value, column)


def in_bounds(board: Board, row: int, column: int, value: int, horizontal: bool):
    if horizontal:
        column = value
    else:
        row = value
    return 0 <= row < board.rows and 0 <= column < board.columns


if __name__ == '__main__':
    kakuro()
