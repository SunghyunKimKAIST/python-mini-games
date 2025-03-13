import tkinter as tk
import random
import math
from pathlib import Path
from lib.aspect import Tk_aspect

FONT = 'Helvetica'

"""
DB structure

[0]: width[0] * 256
[1]: width[1]
[2]: height[0] * 256
[3]: height[1]
[4]: geo_x // 256
[5]: geo_x % 256
[6]: geo_y // 256
[7]: geo_y % 256
[8]: (score/4) // 256
[9]: (score/4) % 256

board = n.bit_length() - 1 if n else 0
"""
IDX = 10

def int_to_db(i):
    return [i >> 8, i & 255]

def db_to_int(upper, lower):
    return (upper << 8) | lower

class Game2048:
    def __init__(self, db):
        width, height, geo_x, geo_y, self.score, board = db_to_data(db)

        self.window = Tk_aspect(10, 12, geo_x, geo_y, width, height, self.size_change)
        self.window.title('2048')

        self.reset_btn = tk.Button(self.window, command=self.reset, text='RESET', font=(FONT, 14))
        self.reset_btn.place(relx=1/3, relwidth=1/3, relheight=1/12)

        self.board = [[board[i*4+j] for j in range(4)] for i in range(4)]

        self.label = [[0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                self.label[i][j] = tk.Label(self.window, font=(FONT, 20))
                self.label[i][j].place(relx=j/4, rely=1/12 + i*5/24, relwidth=1/4, relheight=5/24)

        self.score_label = tk.Label(self.window, font=(FONT, 14))
        self.score_label.place(rely=10/11, relwidth=1, relheight=1/12)

        if not any(board):
            self.add_random_tile()
            self.add_random_tile()

        self.update_ui()

        self.window.bind('<Key>', self.key_pressed)
        self.window.bind('<Escape>', self.close_game)
        self.window.bind('<Tab>', self.close_game)
        self.window.bind('<Alt_L>', self.close_game)
        self.window.protocol('WM_DELETE_WINDOW', self.close_game)

    def add_random_tile(self):
        empty_cells = [(i, j) for i in range(4) for j in range(4) if self.board[i][j] == 0]
        if empty_cells:
            i, j = random.choice(empty_cells)
            self.board[i][j] = 2 if random.random() < 0.9 else 4

    def update_ui(self):
        for i in range(4):
            for j in range(4):
                cell_value = self.board[i][j]
                if cell_value >= 8000:
                    cell_color = '#00FFFF'
                else:
                    cell_color = '#%02x%02x%02x' % (255, 255 - 20*int(math.log2(cell_value+1)), 255 - 20*int(math.log2(cell_value+1)))
                self.label[i][j].config(text=str(cell_value), bg=cell_color)

        self.score_label['text'] = 'Score: ' + str(self.score)

    def key_pressed(self, event):
        key = event.keysym
        if key in ['Up', 'Down', 'Left', 'Right']:
            before = self.board
            self.move(key)
            if before != self.board:
                self.add_random_tile()
                self.update_ui()

    def move(self, direction):
        if direction == 'Up':
            self.board = [list(row) for row in zip(*self.board)]
            self.board = [self.move_left(row) for row in self.board]
            self.board = [list(row) for row in zip(*self.board)]
        elif direction == 'Down':
            self.board = [list(row[::-1]) for row in zip(*self.board)]
            self.board = [self.move_left(row) for row in self.board]
            self.board = [list(row) for row in zip(*self.board)][::-1]
        elif direction == 'Left':
            self.board = [self.move_left(row) for row in self.board]
        elif direction == 'Right':
            self.board = [row[::-1] for row in self.board]
            self.board = [self.move_left(row) for row in self.board]
            self.board = [row[::-1] for row in self.board]

    def move_left(self, row):
        row = [val for val in row if val != 0]
        i = 0
        while i < len(row) - 1:
            if row[i] == row[i + 1]:
                row[i] *= 2
                self.score += row[i]
                del row[i + 1]
            i += 1
        row += [0] * (4 - len(row))
        return row

    def run(self):
        self.window.mainloop()

    def size_change(self, size):
        font = FONT, round(size / (11 * 14))
        for row in self.label:
            for l in row:
                l['font'] = font

        font = FONT, round(size / (11 * 20))
        self.reset_btn['font'] = font
        self.score_label['font'] = font

    def close_game(self, _=None):
        s = self.window.geometry()
        self.width, s = s.split('x')
        self.width = int(self.width)
        self.height, self.geo_x, self.geo_y = map(int, s.split('+'))

        self.window.destroy()

    def export(self):
        db = [0] * (IDX + 16)
        db[0:2] = int_to_db(self.width)
        db[2:4] = int_to_db(self.height)
        db[4:6] = int_to_db(self.geo_x)
        db[6:8] = int_to_db(self.geo_y)
        db[8:10] = int_to_db(self.score // 4)

        i = IDX
        for row in self.board:
            for n in row:
                db[i] = n.bit_length() - 1 if n else 0
                i += 1

        return db

    def reset(self):
        self.board = [[0]*4 for _ in range(4)]
        self.score = 0

        self.add_random_tile()
        self.add_random_tile()

        self.update_ui()


if Path('db').exists():
    with open('db', 'rb', 0) as dbfile:
        db = dbfile.readall()

else:
    db = int_to_db(280) \
       + int_to_db(336) \
       + int_to_db(1300) \
       + int_to_db(300) \
       + [0, 0] \
       + [0] * 16

def db_to_data(db):
    width = db_to_int(db[0], db[1])
    height = db_to_int(db[2], db[3])
    geo_x = db_to_int(db[4], db[5])
    geo_y = db_to_int(db[6], db[7])
    score = db_to_int(db[8], db[9]) * 4

    board = [1 << n if n else 0 for n in db[IDX:]]

    return width, height, geo_x, geo_y, score, board

game = Game2048(db)
game.run()

def print_db(db, board_flag=True):
    width, height, geo_x, geo_y, score, board = db_to_data(db)

    print(f'width: {width}',
          f'height: {height}',
          f'geo_x: {geo_x}',
          f'geo_y: {geo_y}',
          f'score: {score}',
          sep='\n')

    if board_flag:
        i = 0
        for _ in range(4):
            for _ in range(4):
                print(f'{board[i]:5}', end=' ')
                i += 1
            print()

with open('db', 'wb', 0) as dbfile:
    db = game.export()
    # print_db(db)
    dbfile.write(bytes(db))
