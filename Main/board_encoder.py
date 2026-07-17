import numpy as np
import chess


def encode_board(board):
    """Encode a python-chess Board into a (17, 8, 8) numpy array of piece, side-to-move, and castling-right planes."""
    if not isinstance(board, chess.Board):
        raise TypeError("board must be a python-chess Board")

    planes = np.zeros((17, 8, 8), dtype=np.uint8)
    piece_order = [
        1,
        2,
        3,
        4,
        5,
        6,
    ]

    for plane_index, piece_type in enumerate(piece_order):
        for square in chess.SquareSet(chess.BB_ALL):
            piece = board.piece_at(square)
            if piece is None:
                continue
            if piece.piece_type != piece_type:
                continue
            row = chess.square_rank(square)
            col = chess.square_file(square)
            if piece.color == chess.WHITE:
                planes[plane_index, row, col] = 1
            else:
                planes[plane_index + 6, row, col] = 1

    planes[12] = 1 if board.turn == chess.WHITE else 0

    castling_planes = [
        (13, chess.WHITE, chess.BB_H1),
        (14, chess.WHITE, chess.BB_A1),
        (15, chess.BLACK, chess.BB_H8),
        (16, chess.BLACK, chess.BB_A8),
    ]

    for plane_index, color, rook_side_mask in castling_planes:
        if board.has_castling_rights(color) and (board.castling_rights & rook_side_mask) != 0:
            planes[plane_index] = 1
        else:
            planes[plane_index] = 0

    return planes


if __name__ == "__main__":
    board = chess.Board()
    encoded = encode_board(board)
    print(f"Shape: {encoded.shape}")
    print(f"Total ones: {int(encoded.sum())}")

    labels = [
        "White Pawn",
        "White Knight",
        "White Bishop",
        "White Rook",
        "White Queen",
        "White King",
        "Black Pawn",
        "Black Knight",
        "Black Bishop",
        "Black Rook",
        "Black Queen",
        "Black King",
    ]

    for index, label in enumerate(labels):
        print(f"{label}: {int(encoded[index].sum())}")

    side_to_move_plane = encoded[12]
    print(f"Side to move plane unique values: {np.unique(side_to_move_plane)}")

    castling_labels = [
        "White Kingside",
        "White Queenside",
        "Black Kingside",
        "Black Queenside",
    ]
    for index, label in enumerate(castling_labels, start=13):
        print(f"{label} plane unique values: {np.unique(encoded[index])}")

    board_without_castling = chess.Board("4k3/8/8/8/8/8/8/4K2R b - - 0 1")
    encoded_no_castling = encode_board(board_without_castling)
    print(f"No-castling position shape: {encoded_no_castling.shape}")
    for index, label in enumerate(castling_labels, start=13):
        print(f"{label} plane unique values (no castling): {np.unique(encoded_no_castling[index])}")

    legal_moves = list(board.legal_moves)
    if legal_moves:
        board.push(legal_moves[0])
        encoded_after_move = encode_board(board)
        print(f"After one legal White move, shape: {encoded_after_move.shape}")
        print(f"Side to move plane unique values after move: {np.unique(encoded_after_move[12])}")
        print(f"Side-to-move plane changed from all 1s to all 0s: {np.array_equal(encoded[12], np.ones((8, 8), dtype=np.uint8)) and np.array_equal(encoded_after_move[12], np.zeros((8, 8), dtype=np.uint8))}")
