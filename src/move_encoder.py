import chess


PROMOTION_OFFSET = 4096
PROMOTION_PIECE_TYPES = 4
PROMOTION_PAIR_COUNT = 44
TOTAL_CLASSES = PROMOTION_OFFSET + PROMOTION_PAIR_COUNT * PROMOTION_PIECE_TYPES

PROMOTION_PAIRS = [
    (chess.parse_square("a7"), chess.parse_square("a8")),
    (chess.parse_square("b7"), chess.parse_square("b8")),
    (chess.parse_square("c7"), chess.parse_square("c8")),
    (chess.parse_square("d7"), chess.parse_square("d8")),
    (chess.parse_square("e7"), chess.parse_square("e8")),
    (chess.parse_square("f7"), chess.parse_square("f8")),
    (chess.parse_square("g7"), chess.parse_square("g8")),
    (chess.parse_square("h7"), chess.parse_square("h8")),
    (chess.parse_square("a2"), chess.parse_square("a1")),
    (chess.parse_square("b2"), chess.parse_square("b1")),
    (chess.parse_square("c2"), chess.parse_square("c1")),
    (chess.parse_square("d2"), chess.parse_square("d1")),
    (chess.parse_square("e2"), chess.parse_square("e1")),
    (chess.parse_square("f2"), chess.parse_square("f1")),
    (chess.parse_square("g2"), chess.parse_square("g1")),
    (chess.parse_square("h2"), chess.parse_square("h1")),
    (chess.parse_square("a7"), chess.parse_square("b8")),
    (chess.parse_square("b7"), chess.parse_square("a8")),
    (chess.parse_square("b7"), chess.parse_square("c8")),
    (chess.parse_square("c7"), chess.parse_square("b8")),
    (chess.parse_square("c7"), chess.parse_square("d8")),
    (chess.parse_square("d7"), chess.parse_square("c8")),
    (chess.parse_square("d7"), chess.parse_square("e8")),
    (chess.parse_square("e7"), chess.parse_square("d8")),
    (chess.parse_square("e7"), chess.parse_square("f8")),
    (chess.parse_square("f7"), chess.parse_square("e8")),
    (chess.parse_square("f7"), chess.parse_square("g8")),
    (chess.parse_square("g7"), chess.parse_square("f8")),
    (chess.parse_square("g7"), chess.parse_square("h8")),
    (chess.parse_square("h7"), chess.parse_square("g8")),
    (chess.parse_square("a2"), chess.parse_square("b1")),
    (chess.parse_square("b2"), chess.parse_square("a1")),
    (chess.parse_square("b2"), chess.parse_square("c1")),
    (chess.parse_square("c2"), chess.parse_square("b1")),
    (chess.parse_square("c2"), chess.parse_square("d1")),
    (chess.parse_square("d2"), chess.parse_square("c1")),
    (chess.parse_square("d2"), chess.parse_square("e1")),
    (chess.parse_square("e2"), chess.parse_square("d1")),
    (chess.parse_square("e2"), chess.parse_square("f1")),
    (chess.parse_square("f2"), chess.parse_square("e1")),
    (chess.parse_square("f2"), chess.parse_square("g1")),
    (chess.parse_square("g2"), chess.parse_square("f1")),
    (chess.parse_square("g2"), chess.parse_square("h1")),
    (chess.parse_square("h2"), chess.parse_square("g1")),
]
PROMOTION_PAIR_TO_INDEX = {pair: index for index, pair in enumerate(PROMOTION_PAIRS)}
PROMOTION_ORDER = {
    chess.QUEEN: 0,
    chess.ROOK: 1,
    chess.BISHOP: 2,
    chess.KNIGHT: 3,
}


def encode_move(move):
    """Encode a python-chess Move into an integer."""
    if not isinstance(move, chess.Move):
        raise TypeError("move must be a python-chess Move")

    if move.promotion is None:
        return move.from_square * 64 + move.to_square

    pair = (move.from_square, move.to_square)
    if pair not in PROMOTION_PAIR_TO_INDEX:
        raise ValueError(f"Unsupported promotion move: {move.uci()}")

    pair_index = PROMOTION_PAIR_TO_INDEX[pair]
    promo_index = PROMOTION_ORDER[move.promotion]
    return PROMOTION_OFFSET + pair_index * PROMOTION_PIECE_TYPES + promo_index


def decode_move(encoded_value, board=None):
    """Decode an encoded move integer back into a python-chess Move."""
    if not isinstance(encoded_value, int):
        raise TypeError("encoded_value must be an integer")

    if board is None:
        board = chess.Board()

    if encoded_value < PROMOTION_OFFSET:
        from_square = encoded_value // 64
        to_square = encoded_value % 64
        move = chess.Move(from_square, to_square)
        if move in board.legal_moves:
            return move
        raise ValueError(f"Encoded move {encoded_value} is not legal in the provided board")

    pair_index = (encoded_value - PROMOTION_OFFSET) // PROMOTION_PIECE_TYPES
    promo_index = (encoded_value - PROMOTION_OFFSET) % PROMOTION_PIECE_TYPES
    if pair_index >= len(PROMOTION_PAIRS):
        raise ValueError(f"Encoded promotion move {encoded_value} is out of range")

    promotion_piece = {value: piece for piece, value in PROMOTION_ORDER.items()}[promo_index]
    from_square, to_square = PROMOTION_PAIRS[pair_index]
    move = chess.Move(from_square, to_square, promotion=promotion_piece)
    if move in board.legal_moves:
        return move
    raise ValueError(f"Encoded promotion move {encoded_value} is not legal in the provided board")


if __name__ == "__main__":
    test_moves = [
        "e2e4",
        "g1f3",
        "e7e5",
        "b8c6",
        "e7e8q",
        "e7e8r",
        "e7e8b",
        "e7e8n",
        "e2e1q",
        "e2e1r",
        "e2e1b",
        "e2e1n",
        "d7c8q",
        "d7c8r",
        "d7c8b",
        "d7c8n",
    ]
    boards = {
        "e2e4": chess.Board(),
        "g1f3": chess.Board(),
        "e7e5": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"),
        "b8c6": chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"),
        "e7e8q": chess.Board("7k/4P3/7K/8/8/8/8/8 w - - 0 1"),
        "e7e8r": chess.Board("7k/4P3/7K/8/8/8/8/8 w - - 0 1"),
        "e7e8b": chess.Board("7k/4P3/7K/8/8/8/8/8 w - - 0 1"),
        "e7e8n": chess.Board("7k/4P3/7K/8/8/8/8/8 w - - 0 1"),
        "e2e1q": chess.Board("7k/8/8/8/8/8/4p3/7K b - - 0 1"),
        "e2e1r": chess.Board("7k/8/8/8/8/8/4p3/7K b - - 0 1"),
        "e2e1b": chess.Board("7k/8/8/8/8/8/4p3/7K b - - 0 1"),
        "e2e1n": chess.Board("7k/8/8/8/8/8/4p3/7K b - - 0 1"),
        "d7c8q": chess.Board("7k/3P4/7K/8/8/8/8/8 w - - 0 1"),
        "d7c8r": chess.Board("7k/3P4/7K/8/8/8/8/8 w - - 0 1"),
        "d7c8b": chess.Board("7k/3P4/7K/8/8/8/8/8 w - - 0 1"),
        "d7c8n": chess.Board("7k/3P4/7K/8/8/8/8/8 w - - 0 1"),
    }

    print(f"Total classes: {TOTAL_CLASSES}")
    print()

    for uci in test_moves:
        move = chess.Move.from_uci(uci)
        board = boards[uci]
        encoded = encode_move(move)
        decoded = decode_move(encoded, board)
        print(f"Original: {uci}")
        print(f"Encoded: {encoded}")
        print(f"Decoded: {decoded.uci()}")
        print(f"Matches: {decoded == move}")
        print()
