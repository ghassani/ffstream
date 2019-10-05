from .core import Application, Command, CommandArgumentParser
import sys
import curses
import curses.panel
from .version import Version

class TestbedCommand(Command):
	def __init__(self, application: Application, parser: CommandArgumentParser = None):
		super().__init__(application, parser)
		self._screen = None
		self._windows = {
			'title': None,
			'info': None,
			'playlist': None,
			'encoder': None,
			'decoder': None,
		}
		self._panels = []

	def name(self):
		return "test"

	def description(self):
		return "TEST"

	def init(self):
		self.set_args(self.parser().parse_args(sys.argv[2:]))

	def run(self):
		try:
			curses.wrapper(self.main)
		except Exception as e:
			print(e)

		return Command.COMMAND_SUCCESS

	def main(self, screen):
		self._screen = screen

		curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_RED)
		curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLUE)
		curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)
		curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_YELLOW)

		screen.clear()
		screen.bkgd(curses.A_NORMAL, curses.color_pair(0))

		self._windows['title'] = screen.subwin(2, curses.COLS, 0, 0)
		self._windows['title'].bkgd(curses.A_NORMAL, curses.color_pair(2))
		self._windows['title'].addstr('%s - %s' % (self.application().name(), Version.version()))

		self._windows['info'] = screen.subwin(2, curses.COLS, 3, 0)
		self._windows['info'].bkgd(curses.A_NORMAL, curses.color_pair(3))
		self._windows['info'].addstr('Currently Playing: [TITLE] - [PATH]')

		self._windows['playlist'] = screen.subwin(curses.LINES-6, int(curses.COLS/3), 6, 0)
		self._windows['playlist'].bkgd(curses.A_NORMAL, curses.color_pair(4))
		self._windows['playlist'].addstr('Playlist')

		self._windows['encoder'] = screen.subwin(curses.LINES-6, int(curses.COLS/3), 6, int(curses.COLS/3)+1)
		self._windows['encoder'].bkgd(curses.A_NORMAL, curses.color_pair(2))
		self._windows['encoder'].addstr('ENCODER OUTPUT')

		self._windows['decoder'] = screen.subwin(curses.LINES - 6, int(curses.COLS/3), 6, int((curses.COLS/3) * 2)+1)
		self._windows['decoder'].bkgd(curses.A_NORMAL, curses.color_pair(3))
		self._windows['decoder'].addstr('DECODER OUTPUT')

		#a = self._window.subwin(curses.LINES, int(curses.COLS/2), 0, int(curses.COLS/2))

		#a.bkgd(curses.A_NORMAL, curses.color_pair(2))
		#a.insstr('aaaaa')
		#a.insstr('bbbbb')



		while True:
			screen.refresh()
			self._windows['title'].clear()

