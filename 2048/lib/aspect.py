from tkinter import Tk

def configure(e):
    if not isinstance(e.widget, Tk):
        return

    tk = e.widget

    if (tk.width, tk.height) == (e.width, e.height):
        return

    if tk.width == e.width:
        tk.height = e.height

        width = e.height * tk.r_width / tk.r_height
        height = e.height

    elif tk.height == e.height:
        tk.width = e.width

        width = e.width
        height = e.width * tk.r_height / tk.r_width

    else:
        tk.width, tk.height = e.width, e.height

        size = (e.width * tk.r_height + e.height * tk.r_width) / 2
        width = size / tk.r_height
        height = size / tk.r_width

    if width < 120:
        width = 120
        height = width * tk.r_height / tk.r_width

    geo_x = e.x + e.width / 2
    geo_y = e.y + e.height / 2

    tk.geometry(f'{round(width)}x{round(height)}'
                f'+{round(geo_x - width / 2)}+{round(geo_y - height / 2)}')

    if tk.callback:
        tk.callback(width * tk.r_height)

class Tk_aspect(Tk):
    def __init__(self, r_width, r_height, geo_x, geo_y, width, height, callback=None):
        super().__init__()

        self.r_width = r_width
        self.r_height = r_height
        self.width = width
        self.height = height

        self.geometry(f'{width}x{height}+{geo_x}+{geo_y}')

        self.callback = callback
        self.bind('<Configure>', configure)

if __name__ == '__main__':
    tk = Tk_aspect(1, 1, 1000, 500, 150, 150)
    tk.mainloop()
