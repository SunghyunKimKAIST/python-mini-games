import tkinter as tk
from threading import Lock
from collections import namedtuple

from lib.vector import Vector


MSPF = 10
G = Vector(0, 0.1)

WIDTH = 500
HEIGHT = 500

CENTER = Vector(WIDTH / 2, HEIGHT / 2)
R = 200


Shape = namedtuple('Shape', ['fill', 'outline', 'width'], defaults=('', 0))

BALL_R = 10
BALL_R2 = BALL_R * 2
BALL_SHAPE = Shape('white')

BALL_COOLTIME = 20
BALL_N = 100

R_B = R - BALL_R


class Ball:
    def __init__(self, pos):
        self.pos = pos
        self.pos_b = pos  # 초기 속도
        self.pos_draw = pos
        self.id = draw_circle(self.pos, BALL_R, BALL_SHAPE)

        balls.append(self)

    def next_pos(self):
        self.pos, self.pos_b = 2*self.pos - self.pos_b + G, self.pos
        d = self.pos - self.pos_draw
        canvas.move(self.id, d.x, d.y)
        self.pos_draw = self.pos

    def constrain(self):
        d = self.pos - CENTER
        if abs(d) > R_B:
            self.pos = CENTER + d.norm() * R_B


def draw_circle(pos, size, shape):
    return canvas.create_oval(*pos.bbox(size), **shape._asdict())

def next_frame():
    global ball_next

    with lock:
        try:
            id = root.after(MSPF, next_frame)

            for ball in balls:
                ball.next_pos()

            for ball in balls:
                ball.constrain()

            # solve collision
            for i, b1 in enumerate(balls):
                for b2 in balls[i+1:]:
                    d = b1.pos - b2.pos
                    d_len = abs(d)
                    if d_len < BALL_R2:
                        dd = d * ((BALL_R - d_len/2) / d_len)
                        b1.pos += dd
                        b2.pos -= dd

            if len(balls) < BALL_N:
                ball_next -= 1
                if ball_next <= 0:
                    ball_next = BALL_COOLTIME
                    Ball(Vector(400, 200))

            root.update_idletasks()

        except Exception as e:
            root.after_cancel(id)
            raise e


root = tk.Tk()
root.geometry(f'{WIDTH + 4}x{HEIGHT + 4}+1000+250')
root.resizable(False, False)

canvas = tk.Canvas(width=WIDTH, height=HEIGHT, bg='white')
canvas.pack()

draw_circle(CENTER, R, Shape('black'))

balls = []

lock = Lock()

ball_next = 0
next_frame()
root.mainloop()
