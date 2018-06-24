import unittest

modules_to_test = (
    "bitboard",
    "database",
    "draw",
    "eval",
    "fen",
    "frc_castling",
    "frc_movegen",
    "move",
    "movegen",
    "pgn",
    "atomic",
    "crazyhouse",
    "losers",
    "sittuyin",
    "placement",
    "suicide",
    "zobrist",
    "polyglot",
    'ficsmanagers',
    'ficsplay',
    'ficsobserve',
    'ficslecturebot',
    'ficspuzzlebot',
    'analysis',
    'selfplay',
    'engine',
    'savegame',
    'dialogs',
    'learn',
)


def suite():
    tests = unittest.TestSuite()
    for module in map(__import__, modules_to_test):
        tests.addTest(unittest.findTestCases(module))
    return tests


if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
