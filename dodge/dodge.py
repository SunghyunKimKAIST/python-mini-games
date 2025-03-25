import tkinter as tk
from threading import Lock
import random as rd
from collections import namedtuple
from types import SimpleNamespace
from decimal import Decimal

from lib.vector import Vector


FPS = 100
MSPF = 1000 // FPS
SPF = Decimal('0.01')  # 수동으로 변경해야 함

WIDTH = 500
HEIGHT = 500


Shape = namedtuple('Shape', ['fill', 'outline', 'width'], defaults=('', 0))

PLAYER_SIZE = 3
PLAYER_SPEED = 1.5
PLAYER_SHAPE = Shape('white')
PLAYER_POS_INIT = Vector(WIDTH / 2, HEIGHT / 2)


MOB_SIZE = 3

MOB_LINEAR_SPEED_MIN = 0.5
MOB_LINEAR_SPEED_MAX = 2
MOB_LINEAR_SHAPE = Shape('yellow', 'red', 1.5)
MOB_LINEAR_N = 50

MOB_FOLLOWER_SPEED = 2
MOB_FOLLOWER_ACC = 0.015
MOB_FOLLOWER_SHAPE = Shape('light blue', 'blue', 1)


class Player:
    def __init__(self):
        self.pos = PLAYER_POS_INIT
        self.id = draw_circle(self.pos, PLAYER_SIZE, PLAYER_SHAPE)

    def next_frame(self, d):
        d *= PLAYER_SPEED

        # tkinter canvas jot bug
        lc = 2
        hc = -1
        pos = (self.pos + d).bound(PLAYER_SIZE + lc,
                                   PLAYER_SIZE + lc,
                                   WIDTH - PLAYER_SIZE - hc,
                                   HEIGHT - PLAYER_SIZE - hc)
        d = pos - self.pos
        canvas.move(self.id, d.x, d.y)
        self.pos = pos


class Mob:
    def __init__(self, shape, reset=False):
        self.pos = Vector.rand_boundary(WIDTH, HEIGHT)
        self.id = draw_circle(self.pos, MOB_SIZE, shape, 'mob')

        if not reset:
            mobs.append(self)

    def next_frame(self):
        raise NotImplementedError


class MobLinear(Mob):
    def __init__(self, *, reset=False):
        super().__init__(MOB_LINEAR_SHAPE, reset)
        self.d = Vector.rand() * rd.uniform(MOB_LINEAR_SPEED_MIN, MOB_LINEAR_SPEED_MAX)

    def next_frame(self):
        pos = (self.pos + self.d) % (WIDTH, HEIGHT, MOB_SIZE)
        d = pos - self.pos
        canvas.move(self.id, d.x, d.y)
        self.pos = pos


class MobFollower(Mob):
    def __init__(self):
        super().__init__(MOB_FOLLOWER_SHAPE)
        self.heading = Vector.rand()

    def next_frame(self):
        self.heading += (player.pos - self.pos).norm() * MOB_FOLLOWER_ACC
        self.heading = self.heading.norm()
        d = self.heading * MOB_FOLLOWER_SPEED
        self.pos += d
        canvas.move(self.id, d.x, d.y)


class Spawner:
    def __init__(self, mob_class, cooltime, inittime):
        self.mob_class = mob_class

        self.cooltime = cooltime
        self.next = inittime

    def next_frame(self):
        self.next -= 1
        if self.next <= 0:
            self.next = self.cooltime

            self.mob_class()


def draw_circle(pos, size, shape, tag=None):
    return canvas.create_oval(*pos.bbox(size), **shape._asdict(), tag=tag)

def key_press(e):
    if e.keysym == 'r' and gameover:
        restart()

    key_set.add(e.keysym)

def key_release(e):
    key_set.remove(e.keysym)

key_direction = [(('w', 'Up'), (0, -1)),
                 (('a', 'Left'), (-1, 0)),
                 (('s', 'Down'), (0, 1)),
                 (('d', 'Right'), (1, 0))]

def next_frame():
    global gameover

    # 현재 프레임 연산이 끝나지 않았는데 다음 프레임 연산이 먼저 시작되는 것을 방지
    with lock:
        try:
            if gameover:
                return
            id = root.after(MSPF, next_frame)

            d = Vector(0, 0)
            for keys, direction in key_direction:
                if any(key in key_set for key in keys):
                    d += Vector(*direction)
            d = d.norm()

            player.next_frame(d)
            spawner.next_frame()
            for mob in mobs:
                mob.next_frame()

            # 충돌 체크
            pbbox = player.pos.bbox(PLAYER_SIZE + MOB_SIZE)
            for mob in mobs:
                if mob.pos.isin(*pbbox):
                    if abs(player.pos - mob.pos) <= PLAYER_SIZE + MOB_SIZE:
                        root.after_cancel(id)
                        canvas.create_text(WIDTH / 2, HEIGHT / 2 - 20,
                                           text='YOU DIED',
                                           font=('맑은 고딕', 50), fill='red',
                                           tags='end')
                        canvas.create_text(WIDTH / 2, HEIGHT / 2 + 45,
                                           text='PRESS R TO RESTART',
                                           font=('맑은 고딕', 15), fill='yellow',
                                           tags='end')
                        gameover = True

            timer.t += SPF
            canvas.itemconfig(timer.id, text=f'{timer.t}s')

            root.update_idletasks()
        except Exception as e:
            root.after_cancel(id)
            raise e

def mob_rand():
    pos = Vector.rand_boundary(WIDTH, HEIGHT)
    d = Vector.rand()
    return pos, d

def restart():
    global gameover, mobs

    canvas.delete(player.id, 'mob', 'end')

    player.__init__()
    mobs = mobs[:MOB_LINEAR_N]  # bad code
    for mob in mobs:
        mob.__init__(reset=True)

    timer.t = 0

    gameover = False
    next_frame()


root = tk.Tk()
root.geometry(f'{WIDTH + 4}x{HEIGHT + 4}+1000+250')
root.resizable(False, False)

canvas = tk.Canvas(bg='black', width=WIDTH, height=HEIGHT)
canvas.pack()

player = Player()
mobs = []

key_set = set()
root.bind('<KeyPress>', key_press)
root.bind('<KeyRelease>', key_release)

lock = Lock()

for _ in range(MOB_LINEAR_N):
    MobLinear()

spawner = Spawner(MobFollower, 100, 100)

timer = SimpleNamespace(id=canvas.create_text(WIDTH / 2, 12, text='0.00s',
                                              font=('맑은 고딕', 12), fill='yellow'),
                        t=0)

gameover = False
next_frame()
root.mainloop()
