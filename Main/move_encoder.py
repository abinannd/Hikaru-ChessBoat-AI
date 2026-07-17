import chess


PROMOTION_OFFSET = 4096
PROMOTION_CLASSES = 4
TOTAL_CLASSES = PROMOTION_OFFSET + PROMOTION_CLASSES * 64 * 64


def encode_move(move):
    """Encode a python-chess Move into an integer.

    Non-promotion moves keep the existing 4096-class mapping:
    from_square * 64 + to_square.

    Promotion moves use the same base for source/destination and then add a
    promotion-specific offset so that moves with the same source and destination
    but different promotion pieces receive distinct class IDs.
    """
    if not isinstance(move, chess.Move):
        raise TypeError("move must be a python-chess Move")

    if move.promotion is None:
        return move.from_square * 64 + move.to_square

    promotion_order = {
        chess.QUEEN: 0,
        chess.ROOK: 1,
        chess.BISHOP: 2,
        chess.KNIGHT: 3,
    }
    promo_index = promotion_order[move.promotion]
    base = move.from_square * 64 + move.to_square
    return PROMOTION_OFFSET + promo_index * 4096 + base


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

    promo_index = (encoded_value - PROMOTION_OFFSET) // 4096
    base = (encoded_value - PROMOTION_OFFSET) % 4096
    from_square = base // 64
    to_square = base % 64
    promotion_order = {
        0: chess.QUEEN,
        1: chess.ROOK,
        2: chess.BISHOP,
        3: chess.KNIGHT,
    }
    promotion_piece = promotion_order[promo_index]
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
        "e2e1n",
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
        "e2e1n": chess.Board("7k/8/8/8/8/8/4p3/7K b - - 0 1"),
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
