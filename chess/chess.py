from tkinter import *
from enum import Enum
from copy import deepcopy
from pathlib import Path


CELL_SIZE = 100
BOARD_SIZE = CELL_SIZE * 8
BORDER_RATIO = 0.03
REL_SIZE = 1 - 2*BORDER_RATIO
ICON_SIZE = 40
HEADER_HEIGHT = 54
DEAD_HEIGHT = 60


BG_LIGHT = 'white'
BG_DARK = 'lightgrey'
EDGE_FOCUS = 'red'
EDGE_REACHABLE = 'blue'
EDGE_BEFORE = 'lightgreen'


DB_BEFORE_NULL = 0b1000000


class Color(Enum):
    WHITE = 0
    BLACK = 1

    def opponent(self):
        return Color(not self.value)

    def s(self):
        return 'White' if self == Color.WHITE else 'Black'


class Kind(Enum):
    KING = 1
    QUEEN = 2
    ROOK = 3
    BISHOP = 4
    KNIGHT = 5
    PAWN = 6


class Piece:
    def __init__(self, kind=None, color=None):
        self.kind = kind
        self.color = color

    def __bool__(self):
        return bool(self.kind)

    def icon(self):
        if not self.kind:
            return ''

        return {Kind.KING: ['♔', '♚'],
                Kind.QUEEN: ['♕', '♛'],
                Kind.ROOK: ['♖','♜'],
                Kind.BISHOP: ['♗','♝'],
                Kind.KNIGHT: ['♘','♞'],
                Kind.PAWN: ['♙','♟'],
                }[self.kind][self.color.value]

    def copy(self):
        return Piece(self.kind, self.color)


def piece_to_byte(piece):
    return piece.kind.value << 1 | piece.color.value if piece else 0

def byte_to_piece(b):
    return Piece(Kind(b >> 1), Color(b & 1)) if b else Piece()

def icon_to_byte(icon):
    return {'♔': 1 << 1 | 0, '♚': 1 << 1 | 1,
            '♕': 2 << 1 | 0, '♛': 2 << 1 | 1,
            '♖': 3 << 1 | 0, '♜': 3 << 1 | 1,
            '♗': 4 << 1 | 0, '♝': 4 << 1 | 1,
            '♘': 5 << 1 | 0, '♞': 5 << 1 | 1,
            '♙': 6 << 1 | 0, '♟': 6 << 1 | 1,
            }[icon]

def byte_to_icon(b):
    return {0 : 'ㅁ',
            1 << 1 | 0 : '♔', 1 << 1 | 1 : '♚',
            2 << 1 | 0 : '♕', 2 << 1 | 1 : '♛',
            3 << 1 | 0 : '♖', 3 << 1 | 1 : '♜',
            4 << 1 | 0 : '♗', 4 << 1 | 1 : '♝',
            5 << 1 | 0 : '♘', 5 << 1 | 1 : '♞',
            6 << 1 | 0 : '♙', 6 << 1 | 1 : '♟',
            }[b]

def idx_to_byte(i, j):
    return i << 3 | j

def byte_to_idx(b):
    return b >> 3, b & 7


class Cell:
    def __init__(self, board, i, j):
        self.board = board
        self.i = i
        self.j = j
        self._ori_bg = BG_DARK if (i + j) & 1 else BG_LIGHT

        frame = Frame(board, height=CELL_SIZE, width=CELL_SIZE, bg=self._ori_bg)
        frame.place(relx=j/8, rely=i/8, relwidth=1/8, relheight=1/8)
        self.frame = frame

        label = Label(frame, bg=self._ori_bg, relief='flat', font=f'TkDefaultFont {ICON_SIZE}')
        label.place(relx=BORDER_RATIO, rely=BORDER_RATIO, relwidth=REL_SIZE, relheight=REL_SIZE)
        self.label = label

        frame.bind('<1>', self.click)
        label.bind('<1>', self.click)

        self.piece = Piece()
        self._reachable = False
        self.before = False

    @property
    def ori_bg(self):
        return EDGE_BEFORE if self.before else self._ori_bg

    @property
    def reachable(self):
        return self._reachable

    @reachable.setter
    def reachable(self, value):
        if self._reachable != value:
            self._reachable = value

            self.frame['bg'] = EDGE_REACHABLE if value else self._ori_bg

    def set_piece(self, kind, color=None):
        self.piece.kind = kind
        self.piece.color = color
        self.label['text'] = self.piece.icon()

    def reachable_cells(self, only_attack=False):
        def append(res, i, j):
            if not 0 <= i < 8 or not 0 <= j < 8:
                return False

            if self.board.cells[i][j].piece.color != self.piece.color:
                res.append((i, j))
                return True

            return False


        if not self.piece:
            return []

        res = []

        if self.piece.kind == Kind.PAWN:
            if self.piece.color == Color.WHITE:
                move = -1
                init_i = 6
                en_passant_i = 3
            else:  # self.piece.color == Color.BLACK
                move = 1
                init_i = 1
                en_passant_i = 4

            if not self.board.cells[self.i + move][self.j].piece:
                append(res, self.i + move, self.j)
                if self.i == init_i and not self.board.cells[self.i + move * 2][self.j].piece:
                    append(res, self.i + move * 2, self.j)

            for j in [self.j - 1, self.j + 1]:
                if 0 <= j < 8 and self.board.cells[self.i + move][j].piece:
                    append(res, self.i + move, j)

            # en passant
            if not only_attack and self.i == en_passant_i:
                before = self.board.before
                if before[0].piece.kind == Kind.PAWN:
                    for j in [self.j - 1, self.j + 1]:
                        if (before[0].i, before[0].j) == (self.i, j) and \
                           (before[1].i, before[1].j) == (self.i + move * 2, j):
                            append(res, self.i + move, j)

        elif self.piece.kind == Kind.KING:
            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i == 0 and j == 0:
                        continue
                    append(res, self.i + i, self.j + j)

            # castling
            if not only_attack:
                # king side
                if self.board.castling[self.piece.color][0] and \
                   not any(self.board.cells[self.i][j].piece for j in [5, 6]) and \
                   not self.board.is_attacked([(self.i, 4), (self.i, 5), (self.i, 6)]):
                    res.append((self.i, 7))

                # queen side
                if self.board.castling[self.piece.color][1] and \
                   not any(self.board.cells[self.i][j].piece for j in [1, 2, 3]) and \
                   not self.board.is_attacked([(self.i, 2), (self.i, 3), (self.i, 4)]):
                    res.append((self.i, 0))

        elif self.piece.kind == Kind.KNIGHT:
            moves = [(2, 1), (1, 2), (-1, 2), (-2, 1),
                     (-2, -1), (-1, -2), (1, -2), (2, -1)]
            for move in moves:
                append(res, self.i + move[0], self.j + move[1])

        else:
            moves = [[(1, 0), (0, 1), (-1, 0), (0, -1)],
                     [(1, 1), (-1, 1), (-1, -1), (1, -1)]]

            if self.piece.kind == Kind.ROOK:
                move_idxs = [0]
            elif self.piece.kind == Kind.BISHOP:
                move_idxs = [1]
            else:  # self.piece.kind == Kind.QUEEN
                move_idxs = [0, 1]

            for move_idx in move_idxs:
                for move in moves[move_idx]:
                    i = self.i + move[0]
                    j = self.j + move[1]

                    while append(res, i, j):
                        if self.board.cells[i][j].piece:
                            break
                        i += move[0]
                        j += move[1]

        if not only_attack:
            kind = self.piece.kind
            color = self.piece.color
            self.piece.kind = None
            self.piece.color = None

            res_reduced = set()
            for (i, j) in res:
                piece = self.board.cells[i][j].piece

                b_kind = piece.kind
                b_color = piece.color
                piece.kind = kind
                piece.color = color
                if kind == Kind.KING:
                    self.board.king_pos[color] = (i, j)

                if not self.board.check_check():
                    res_reduced.add((i, j))

                piece.kind = b_kind
                piece.color = b_color

            self.piece.kind = kind
            self.piece.color = color
            if kind == Kind.KING:
                self.board.king_pos[color] = (self.i, self.j)

            res = res_reduced

        return res

    def can_attack(self, color, res):
        if self.piece.color == color:
            res.append(self.reachable_cells(True))

    def click(self, _):
        if self.board.clicked:
            if self.reachable:
                promotion = False

                piece = self.board.clicked.piece

                if self.piece.color == self.board.turn:
                    # castling
                    if self.j == 7:
                        # king side
                        self.board.cells[self.i][6].set_piece(Kind.KING, piece.color)
                        self.board.cells[self.i][5].set_piece(Kind.ROOK, piece.color)
                        self.board.king_pos[piece.color] = (self.i, 6)

                        self.set_piece(None)
                        self.board.clicked.set_piece(None)

                    else:
                        # queen side
                        self.board.cells[self.i][2].set_piece(Kind.KING, piece.color)
                        self.board.cells[self.i][3].set_piece(Kind.ROOK, piece.color)
                        self.board.king_pos[piece.color] = (self.i, 2)

                        self.set_piece(None)
                        self.board.clicked.set_piece(None)

                    self.board.castling[self.board.turn] = [False] * 2

                else:
                    if piece.kind == Kind.KING:
                        self.board.king_pos[piece.color] = (self.i, self.j)

                        self.board.castling[piece.color] = [False] * 2

                    elif piece.kind == Kind.PAWN:
                        if self.i == 0 or self.i == 7:
                            # promotion
                            promotion = True
                        elif self.j != self.board.clicked.j and not self.piece:
                            # en passant
                            self.board.dead[piece.color]['text'] += self.board.before[0].piece.icon()
                            self.board.before[0].set_piece(None)

                    elif piece.kind == Kind.ROOK:
                        # disable castling when rook moves

                        init_pos = {(0, 0): (Color.BLACK, 1),
                                    (0, 7): (Color.BLACK, 0),
                                    (7, 0): (Color.WHITE, 1),
                                    (7, 7): (Color.WHITE, 0)}

                        rook = init_pos.get((self.board.clicked.i, self.board.clicked.j))

                        if rook:
                            color, side = rook
                            self.board.castling[color][side] = False

                    if self.piece:
                        self.board.dead[piece.color]['text'] += self.piece.icon()

                    self.set_piece(piece.kind, piece.color)
                    self.board.clicked.set_piece(None)

                if promotion:
                    self.board.promotion = True
                    self.board.undo_btn['text'] = ' X '
                    self.board.undo_btn['state'] = 'disabled'
                    self.board.reset_btn['text'] = ' X '
                    self.board.reset_btn['state'] = 'disabled'

                    labels = [Label(self.frame, relief='flat',
                                    font=f'TkDefaultFont {self.board.icon_size // 2}') for _ in range(4)]

                    labels[0]['bg'] = BG_LIGHT
                    labels[1]['bg'] = BG_DARK
                    labels[2]['bg'] = BG_DARK
                    labels[3]['bg'] = BG_LIGHT

                    kinds = [Kind.QUEEN, Kind.ROOK, Kind.BISHOP, Kind.KNIGHT]
                    for (label, kind) in zip(labels, kinds):
                        label['text'] = Piece(kind, self.piece.color).icon()

                    labels[0].place(relx=0, rely=0, relwidth=0.5, relheight=0.5)
                    labels[1].place(relx=0, rely=0.5, relwidth=0.5, relheight=0.5)
                    labels[2].place(relx=0.5, rely=0, relwidth=0.5, relheight=0.5)
                    labels[3].place(relx=0.5, rely=0.5, relwidth=0.5, relheight=0.5)

                    clicked = self.board.clicked

                    def f1(i):
                        def f2(_):
                            for label in labels:
                                label.place_forget()

                            self.set_piece(kinds[i], self.piece.color)
                            self.board.change_turn((self, clicked))
                            self.board.promotion = False
                            self.board.undo_btn['text'] = '봐줘'
                            self.board.undo_btn['state'] = 'normal'
                            self.board.reset_btn['text'] = 'RESET'
                            self.board.reset_btn['state'] = 'normal'

                        return f2

                    for i in range(4):
                        labels[i].bind('<1>', f1(i))

                    self.board.state_label['text'] = 'Promotion!'
                    self.board.before = None
                else:
                    self.board.change_turn((self, self.board.clicked))

            self.board.clicked = None
        else:
            if self.board.promotion:
                return

            if not self.piece:
                return

            if self.piece.color != self.board.turn:
                return

            self.board.clicked = self

"""
DB structure

idx: i << 3 | j
piece: kind << 1 | color

[0]: before[0] idx (0b10000000 if NULL)
[1]: before[1] idx (0b10000000 if NULL)
[2]: turn
[3]: king_pos[WHITE] idx
[4]: king_pos[BLACK] idx
[5]: castling [WHITE][0] << 3 | [WHITE][1] << 2 | \
              [BLACK][0] << 1 | [BLACK][1]

[6 ~ +63]: piece[i] piece
[~]: len(dead[WHITE]) << 4 | len(dead[BLACK])
[~+len(dead[WHITE])]: dead[WHITE] piece
[~+len(dead[BLACK])]: dead[BLACK] piece
"""


class DB:
    def __init__(self, piece, before, turn, king_pos, castling, dead):
        self.piece = piece
        self.before = before
        self.turn = turn
        self.king_pos = king_pos
        self.castling = castling
        self.dead = dead

class Board(Frame):
    def __init__(self, body, db, state_label, dead):
        super().__init__(body, width = BOARD_SIZE, height = BOARD_SIZE)
        self.place(x = 0, y = DEAD_HEIGHT)

        self.cells = [[Cell(self, i, j) for j in range(8)] for i in range(8)]

        self.state_label = state_label
        self.dead = dead

        self._before = None
        self._clicked = None
        self.promotion = False
        self.reset_idx = [0]

        self.db = []

        if db:
            i = 0
            while i < len(db):
                if db[i] == DB_BEFORE_NULL:
                    before = None
                else:
                    i0, j0 = byte_to_idx(db[i])
                    i1, j1 = byte_to_idx(db[i+1])
                    before = (self.cells[i0][j0], self.cells[i1][j1])
                i += 2

                turn = Color(db[i])
                i += 1

                king_pos = {Color.WHITE: byte_to_idx(db[i]), Color.BLACK: byte_to_idx(db[i+1])}
                i += 2

                castling = {Color.WHITE: [bool(db[i] & 8), bool(db[i] & 4)],
                            Color.BLACK: [bool(db[i] & 2), bool(db[i] & 1)]}
                i += 1

                piece = []
                for _ in range(8):
                    piece.append([])
                    for _ in range(8):
                        piece[-1].append(byte_to_piece(db[i]))
                        i += 1

                dead = {Color.WHITE: '', Color.BLACK: ''}

                len_dead_white, len_dead_black = db[i] >> 4, db[i] & 15
                i += 1

                for _ in range(len_dead_white):
                    dead[Color.WHITE] += byte_to_icon(db[i])
                    i += 1

                for _ in range(len_dead_black):
                    dead[Color.BLACK] += byte_to_icon(db[i])
                    i += 1

                self.db.append(DB(piece, before, turn, king_pos, castling, dead))

            self.undo(False)
        else:
            self.turn = Color.WHITE

            self.set_init()

            self.save_db()

            self.foreach_cells(lambda c: setattr(c, '_reachable_cells', c.reachable_cells())
                                         if c.piece.color == Color.WHITE else None)

    @property
    def clicked(self):
        return self._clicked

    @clicked.setter
    def clicked(self, value):
        if value:
            value.frame['bg'] = EDGE_FOCUS

            for (i, j) in value._reachable_cells:
                self.cells[i][j].reachable = True

        elif self._clicked:
            self._clicked.frame['bg'] = self._clicked.ori_bg

            for (i, j) in self._clicked._reachable_cells:
                self.cells[i][j].reachable = False

        self._clicked = value

    @property
    def before(self):
        return self._before

    @before.setter
    def before(self, value):
        if self._before:
            for cell in self._before:
                cell.before = False
                cell.frame['bg'] = cell.ori_bg

        if value:
            for cell in value:
                cell.before = True
                cell.frame['bg'] = EDGE_FOCUS

        self._before = value

    def set_init(self):
        init_pos = [Kind.ROOK,
                    Kind.KNIGHT,
                    Kind.BISHOP,
                    Kind.QUEEN,
                    Kind.KING,
                    Kind.BISHOP,
                    Kind.KNIGHT,
                    Kind.ROOK]

        for j in range(8):
            self.cells[0][j].set_piece(init_pos[j], Color.BLACK)
            self.cells[1][j].set_piece(Kind.PAWN, Color.BLACK)

            for i in range(2, 6):
                self.cells[i][j].set_piece(None)

            self.cells[6][j].set_piece(Kind.PAWN, Color.WHITE)
            self.cells[7][j].set_piece(init_pos[j], Color.WHITE)

        self.king_pos = {Color.WHITE: (7, 4), Color.BLACK: (0, 4)}
        self.castling = {Color.WHITE: [True, True], Color.BLACK: [True, True]}

    def foreach_cells(self, action):
        for row in self.cells:
            for c in row:
                action(c)

    def is_attacked(self, poss):
        opponent = self.turn.opponent()
        res = []

        self.foreach_cells(lambda c: c.can_attack(opponent, res))

        return any(map(
            lambda pos: any(map(
                lambda attackables: pos in attackables,
                res
            )),
            poss
        ))

    def check_check(self):
        return self.is_attacked([self.king_pos[self.turn]])

    def calc_moveables(self):
        def action(c, moveable):
            if c.piece.color == self.turn:
                c._reachable_cells = c.reachable_cells()
                moveable.append(bool(c._reachable_cells))

        moveables = []
        self.foreach_cells(lambda c: action(c, moveables))

        self.state_label['text'] = f'Turn: {self.turn.s()}' if any(moveables) else \
                                   'Checkmate!' if self.check_check() else 'Stalemate'

    def change_turn(self, before):
        self.before = before
        self.turn = self.turn.opponent()

        self.calc_moveables()

        self.save_db()

    def save_db(self):
        piece = []
        for row in self.cells:
            piece.append([])
            for c in row:
                piece[-1].append(c.piece.copy())

        dead = {Color.WHITE: self.dead[Color.WHITE]['text'],
                Color.BLACK: self.dead[Color.BLACK]['text']}

        self.db.append(DB(piece, self.before, self.turn, self.king_pos.copy(),
                          deepcopy(self.castling), dead))

    def undo(self, pop=True):
        if pop:
            if len(self.db) == 1:
                return
            self.db.pop()

        db = self.db[-1]

        if len(self.db) == self.reset_idx[-1]:
            self.reset_idx.pop()

        self.clicked = None
        self.before = db.before
        self.turn = db.turn

        for cells, pieces in zip(self.cells, db.piece):
            for c, piece in zip(cells, pieces):
                c.set_piece(piece.kind, piece.color)

        self.king_pos = db.king_pos
        self.castling = db.castling

        for color, dead in self.dead.items():
            dead['text'] = db.dead[color]

        self.calc_moveables()

    def reset(self):
        self.reset_idx.append(len(self.db))

        self.clicked = None
        self.before = None
        self.turn = Color.WHITE

        self.set_init()

        for color, dead in self.dead.items():
            dead['text'] = ''

        self.calc_moveables()

        self.save_db()

    def export(self):
        db_bin = []

        for db in self.db[self.reset_idx[-1]:]:
            if db.before:
                db_bin += map(lambda c: idx_to_byte(c.i, c.j), db.before)
            else:
                db_bin += [DB_BEFORE_NULL] * 2

            db_bin.append(db.turn.value)

            db_bin.append(idx_to_byte(db.king_pos[Color.WHITE][0], db.king_pos[Color.WHITE][1]))
            db_bin.append(idx_to_byte(db.king_pos[Color.BLACK][0], db.king_pos[Color.BLACK][1]))

            db_bin.append(db.castling[Color.WHITE][0] << 3 |
                          db.castling[Color.WHITE][1] << 2 |
                          db.castling[Color.BLACK][0] << 1 |
                          db.castling[Color.BLACK][1])

            for row in db.piece:
                for piece in row:
                    db_bin.append(piece_to_byte(piece))

            db_bin.append(len(db.dead[Color.WHITE]) << 4 | len(db.dead[Color.BLACK]))

            db_bin += map(icon_to_byte, db.dead[Color.WHITE])
            db_bin += map(icon_to_byte, db.dead[Color.BLACK])

        return db_bin


if Path('db').exists():
    with open('db', 'rb', 0) as dbfile:
        db = dbfile.readall()
else:
    db = []

tk = Tk()
header = Frame()
header.pack()
body = Frame()
body.pack(expand=True, fill='both')

state_label = Label(header, text='Turn: White', font='나눔고딕 20')

f = f'TkDefaultFont {ICON_SIZE}'
dead = {Color.WHITE: Label(body, font=f, anchor='nw'),
        Color.BLACK: Label(body, font=f, anchor='sw')}
dead[Color.WHITE].place(y=BOARD_SIZE + DEAD_HEIGHT, width=BOARD_SIZE)
dead[Color.BLACK].place(width=BOARD_SIZE)

board = Board(body, db, state_label, dead)

board.reset_btn = Button(header, text='RESET', font='나눔고딕 20', command=board.reset)

board.undo_btn = Button(header, text='봐줘', font='나눔고딕 20', command=board.undo)

board.reset_btn.pack(side='left')
state_label.pack(side='left', padx = 50)
board.undo_btn.pack(side='right')


tk.bind('<KeyPress>', lambda _: tk.destroy())


# dead height: font size * 3/2 (default: 60)
# dead / board / dead ratio = 3 / 40 / 3 (default: 60 / 800 / 60)
width, height = BOARD_SIZE, BOARD_SIZE + DEAD_HEIGHT * 2
board.icon_size = ICON_SIZE
def configure(e):
    global width, height

    if e.widget is not body:
        return

    if (width, height) != (e.width, e.height):
        width, height = e.width, e.height

        if width * 23 > height * 20:
            size = height * 20
            x = (width - height * 20 / 23) / 2
            dead_h = height * 3 / 46
            board.place(x = x, y = dead_h)
            board.dead[Color.BLACK].place(x = x, y = 0, height = dead_h)
            board.dead[Color.WHITE].place(x = x, y = height * 43 / 46, height = dead_h)
        else:
            size = width * 23
            y_start = (height - width * 23 / 20) / 2
            dead_h = width * 23 * 3 / 20 / 46
            board.place(x = 0, y = y_start + dead_h)
            board.dead[Color.BLACK].place(x = 0, y = y_start, height = dead_h)
            board.dead[Color.WHITE].place(x = 0, y = y_start + width * 23 * 43 / 20 / 46, height = dead_h)

        board['width'] = size / 23
        board['height'] = size / 23

        icon_size = int(size * ICON_SIZE / 23 / 800)
        board.foreach_cells(lambda c: c.label.config(font = f'TkDefaultFont {icon_size}'))
        board.icon_size = icon_size
        for l in board.dead.values():
            l['font'] = f'TkDefaultFont {icon_size}'

tk.geometry(f'{BOARD_SIZE}x{HEADER_HEIGHT + BOARD_SIZE + DEAD_HEIGHT * 2}+1000+20')
body.bind('<Configure>', configure)

tk.mainloop()


def print_db(db):
    i = 0
    while i < len(db):
        if db[i] == DB_BEFORE_NULL:
            print('before: NULL')
        else:
            print(f'before: {byte_to_idx(db[i])}, {byte_to_idx(db[i+1])}')
        i += 2

        print(f'turn: {Color(db[i]).name}')
        i += 1

        print(f'king pos: WHITE: {byte_to_idx(db[i])}, BLACK: {byte_to_idx(db[i+1])}')
        i += 2

        print(f'castling: WHITE king side: {bool(db[i] & 8)}, queen side: {bool(db[i] & 4)}')
        print(f'          BLACK king side: {bool(db[i] & 2)}, queen side: {bool(db[i] & 1)}')
        i += 1

        print('piece:')
        for _ in range(8):
            for _ in range(8):
                print(f'{byte_to_icon(db[i])}', end='')
                i += 1
            print()

        len_dead_white, len_dead_black = db[i] >> 4, db[i] & 15
        i += 1

        print('dead: WHITE: ', end='')
        for _ in range(len_dead_white):
            print(f'{byte_to_icon(db[i])}', end='')
            i += 1
        print()

        print('      BLACK: ', end='')
        for _ in range(len_dead_black):
            print(f'{byte_to_icon(db[i])}', end='')
            i += 1
        print()

        print('---------------------------------------------')


with open('db', 'wb', 0) as dbfile:
    db = board.export()
    print_db(db)
    dbfile.write(bytes(db))
