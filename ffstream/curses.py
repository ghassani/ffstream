import curses

class Screen:
	def __init__(self, stdscr):
		self._stdscr = stdscr
		self._windows = []

	def stdscr(self):
		return self._stdscr

	def create_window(self, w: int, h: int, x: int, y: int):
		return self._stdscr.subwin(w, h, x, y)

#screen.subwin(2, curses.COLS, 0, 0)

class Window:
	def __init__(self, screen: Screen, w: int, h: int, x: int, y: int):
		self._window = screen.create_window(w, h, x, y)
		self._w = w
		self._h = h
		self._x = x
		self._y = y

	def screen(self) -> Screen:
		return self._screen

	def window(self):
		return self._window
