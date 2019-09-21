import sys
import json
from pathlib import Path
from .core import Application, Command, CommandArgumentParser
from .loader import DirectoryPlaylistLoader, PlaylistLoaderError


"""
GeneratePlaylistCommand
"""


class GeneratePlaylistCommand(Command):
	def __init__(self, application: Application, parser: CommandArgumentParser = None):
		super().__init__(application, parser)

	def name(self):
		return "generate:playlist"

	def description(self):
		return "Generates a playlist from specified directory"

	def init(self):
		self.parser().add_argument('-d', '--directory', help='Directory to scan for video files', required=True)
		self.parser().add_argument('-o', '--output', help='Output location to write playlist to', default="playlist.json")
		self.parser().add_argument('-r', '--recursive', help='Scan directory recursively', action='store_true', default=False)
#		self.parser().add_argument('-R', '--resolve-symlinks', help='Resolve file symlinks to true path', action='store_true', default=False)
		self.parser().add_argument('-f', '--force', help='Force overwrite of playlist', action='store_true', default=False)
		self.parser().add_argument('-s', '--shuffle', help='Shuffle the resulting playlist entries', action='store_true', default=False)
		self.parser().add_argument('-t', '--types', nargs='*', help='Types of video files to consider', default=['mp4', 'webm', 'mkv'])

		self.set_args(self.parser().parse_args(sys.argv[2:]))

	def run(self):
		path = Path(self.args().directory).resolve()

		if not path.is_dir():
			self.logger().error('Directory specified is not a directory')
			return Command.COMMAND_ERROR

		loader = DirectoryPlaylistLoader(self.application())

		try:
			playlist = loader.load(self.args().directory, {
				'recursive': self.args().recursive,
				'types': self.args().types
			})

		except PlaylistLoaderError as e:
			self.logger().error(str(e))
			return Command.COMMAND_ERROR

		if self.args().shuffle is True:
			if self.args().verbose is True:
				self.logger().info('Shuffling playlist entries')
			playlist.shuffle()

		playlist.set_name('My Playlist')
		playlist.set_should_loop(False)
		playlist.set_should_loop_shuffle(False)
		playlist.set_should_shuffle(self.args().shuffle)

		playlist.output().set_destination('rmtp://server.com/application/key')
		playlist.output().resolution().parse_str('1280x720')

		with open(self.args().output, 'w') as output:
			output.write(json.dumps(playlist.serialize(), indent=4, sort_keys=False))
			output.close()

		self.logger().notice('Wrote playlist to %s' % self.args().output)

		return Command.COMMAND_SUCCESS