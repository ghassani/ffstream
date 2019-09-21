import argparse
import sys
from .filter import FilterManager
from .util import Logger, StdOutLogger, TextColor
from ffstream.version import Version


class Application:
	singleton = None

	def __init__(self, parser: 'ArgumentParser' = None):
		self._commands = []
		self._parser = None
		self._logger = StdOutLogger()
		self._filter_manager = FilterManager()

		if parser is not None:
			self._parser = parser

		if Application.singleton is not None:
			raise Exception('Application has already been initialized')

		Application.singleton = self

	def name(self) -> str:
		return 'ffstream'

	def description(self) -> str:
		return ''

	def version(self) -> str:
		return Version.version()

	def run(self):
		"""
		Run the application

		:return: void
		"""

		if self._parser is None:
			commands = []
			for command in self._commands:
				commands.append(command.name())

			self._parser = ArgumentParser(description='ffstream')
			self._parser.add_argument('command', help='The command to execute')
			self._parser.add_argument('-v', '--verbose', help='Display more verbose output', action='store_true', default=False)
			self._parser.add_argument('-q', '--quiet', help='Display less or no output', action='store_true', default=False)

		args = self._parser.parse_args(sys.argv[1:2])

		for command in self._commands:
			if command.name() == args.command:
				command.init()
				if command.run() != Command.COMMAND_SUCCESS:
					return sys.exit(1)
				return sys.exit(0)

		self._parser.print_help()

	def add_command(self, command: 'Command') -> 'Application':
		"""
		Add a command to the application

		:return: Application
		"""

		if not isinstance(command.application(), Application):
			command.set_application(self)

		self._commands.append(command)
		return self

	def commands(self) -> list:
		"""
		Get the available command list

		:return: list of Command
		"""

		return self._commands

	def command(self, name: str):
		"""
		Get a command by name

		:return: Command|None
		"""

		for command in self._commands:
			if command.name() == name:
				return command
		return None

	def parser(self) -> 'ArgumentParser':
		"""
		Get the ArgumentParser

		:return: ArgumentParser
		"""

		return self._parser

	def logger(self) -> Logger:
		"""
		Get the Logger

		:return: Logger
		"""

		return self._logger

	def filter_manager(self) -> FilterManager:
		return self._filter_manager

	def show_banner(self):
		title = '%s v%d.%d.%d' % (self.name(), Version.MAJOR, Version.MINOR, Version.PATCH)
		print('=' * (len(title) + 4))
		print('= ' + title + ' =')
		print('=' * (len(title) + 4))


"""
ArgumentParser
"""


class ArgumentParser(argparse.ArgumentParser):
	def format_help(self):
		base = super().format_help()

		formatter = self._get_formatter()

		for command in Application.singleton.commands():
			formatter.add_text(TextColor.GREEN + command.name() + TextColor.WHITE + " - " + command.description())

		return base + "\r\n" + formatter.format_help()


"""
' Command
"""


class Command:
	COMMAND_SUCCESS = 0
	COMMAND_ERROR = 1

	def __init__(self, application: Application, parser: 'CommandArgumentParser' = None):
		"""
		Command constructor

		:param application: Application
		:param parser: CommandArgumentParser|None
		"""

		self._application = application
		self._parser = parser
		self._args = None

		if not isinstance(self._parser, CommandArgumentParser):
			self._parser = CommandArgumentParser(description=self.description())
			self._parser.add_argument('-v', '--verbose', help='Display more verbose output', action='store_true', default=False)
			self._parser.add_argument('-q', '--quiet', help='Display less or no output', action='store_true', default=False)

	def application(self) -> Application:
		"""
		Get the Application instance

		:returns: Application
		"""

		return self._application

	def set_application(self, application: Application):
		self._application = application
		return self

	def parser(self):
		"""
		Get the CommandArgumentParser instance

		:returns: CommandArgumentParser
		"""

		return self._parser

	def args(self):
		"""
		Get the parsed command arguments

		:returns: object
		"""

		return self._args

	def set_args(self, args) -> 'Command':
		"""
		Set the parsed arguments

		:returns: object
		"""

		self._args = args
		return self

	def logger(self):
		"""
		Get the logger instance

		:returns: Logger
		"""

		return self.application().logger()

	def name(self):
		"""
		Get the name of the command.

		@return str
		"""

		raise Exception('Command:name not implemented')

	def description(self):
		"""
		Get the description of the command.

		@return string
		"""

		raise Exception('Command:description not implemented')

	def init(self):
		"""
		Set up and parse the command options and load command dependencies.

		@return void
		"""

		raise Exception('Command:init not implemented')

	def run(self):
		"""
		Execute the command.

		:returns: void
		:raises Exception: depending on command
		"""

		raise Exception('Command:run not implemented')


"""
CommandArgumentParser
"""


class CommandArgumentParser(argparse.ArgumentParser):
	pass
