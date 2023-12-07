import os
import time


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
    def __init__(self, value):
        self.value = value
        self.availableNumbers = {1, 2, 3, 4, 5, 6, 7, 8, 9}


class Wall:
    def __init__(self, horizontalSum, verticalSum):
        self.horizontalSum = horizontalSum
        self.verticalSum = verticalSum


class Statistics:
    def __init__(self):
        self.attempts = 0


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
    filepath = "kakuro.txt"
    # while True:
    #     filepath = input("Please input the filename: ")
    #     if os.path.isfile(filepath):
    #         break
    with open(filepath, 'r') as file:
        board = []
        for raw_line in file:
            raw_tiles = raw_line.split(",")
            row = []
            for raw_tile in raw_tiles:
                stripped = raw_tile.strip()
                if "\\" in stripped:
                    [verticalSum, horizontalSum] = stripped.split("\\")
                    row.append(Wall(
                        None if horizontalSum == "" else int(horizontalSum),
                        None if verticalSum == "" else int(verticalSum)
                    ))
                else:
                    row.append(Slot(0 if stripped == "" else int(stripped)))
            board.append(row)
    return Board(board)


def backtracking(board: Board, statistics: Statistics):
    emptySlots = []
    for i, row in enumerate(board.board):
        for j, tile in enumerate(row):
            if isinstance(tile, Slot):
                emptySlots.append((i, j))
    recursion(board, emptySlots, 0, statistics)


def recursion(board: Board, emptySlots: [(int, int)], emptySlotIndex, statistics: Statistics):
    if emptySlotIndex >= len(emptySlots):
        return True
    (emptySlotRow, emptySlotColumn) = emptySlots[emptySlotIndex]
    emptySlotTile = board.tileAt(emptySlotRow, emptySlotColumn)
    oldAvailableNumbers = emptySlotTile.availableNumbers.copy()
    emptySlotTile.availableNumbers = available_numbers(board, emptySlotRow, emptySlotColumn)
    for availableNumber in emptySlotTile.availableNumbers:
        emptySlotTile.value = availableNumber
        statistics.attempts += 1
        if recursion(board, emptySlots, emptySlotIndex + 1, statistics):
            return True
        emptySlotTile.value = 0
    emptySlotTile.availableNumbers = oldAvailableNumbers
    return False


def available_numbers(board: Board, row, column):
    horizontalAvailableNumbers = available_numbers_helper(board, row, column, True)
    verticalAvailableNumbers = available_numbers_helper(board, row, column, False)
    return set(horizontalAvailableNumbers).intersection(set(verticalAvailableNumbers))


def available_numbers_helper(board: Board, row: int, column: int, horizontal: bool):
    availableNumbers = board.tileAt(row, column).availableNumbers
    value = row_or_column(row, column, horizontal) - 1
    while isinstance(tile_at_new_row_or_column(board, row, column, value, horizontal), Slot):
        value -= 1
    tile = tile_at_new_row_or_column(board, row, column, value, horizontal)
    requiredSum = tile.horizontalSum if horizontal else tile.verticalSum
    currentSum = 0
    blankSlotsRemaining = 0
    value += 1
    while in_bounds(board, row, column, value, horizontal) and isinstance(tile_at_new_row_or_column(board, row, column, value, horizontal), Slot):
        tile = tile_at_new_row_or_column(board, row, column, value, horizontal)
        currentSum += tile.value
        if tile.value in availableNumbers:
            availableNumbers.remove(tile.value)
        if tile.value == 0:
            blankSlotsRemaining += 1
        value += 1
    remainingSum = requiredSum - currentSum

    if blankSlotsRemaining == 1:
        return [number for number in availableNumbers if number == remainingSum]

    return [number for number in availableNumbers if number <= remainingSum]


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
