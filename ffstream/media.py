import os
import sys
import ffmpeg
from pathlib import Path
from .core import Application, Command, CommandArgumentParser
from .loader import DirectoryPlaylistLoader, PlaylistLoaderError
from .playlist import PlaylistEntry


class FixMediaMetaCommand(Command):
	def __init__(self, application: Application, parser: CommandArgumentParser = None):
		super().__init__(application, parser)

	def name(self):
		return "media:fix-meta"

	def description(self):
		return "Fix missing meta information from media files in directory."

	def init(self):
		self.parser().add_argument('-d', '--directory', help='Directory to scan for video files', required=True)
		self.parser().add_argument('-r', '--recursive', help='Scan directory recursively', action='store_true', default=False)
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

		for entry in playlist.entries():  # type: PlaylistEntry
			if entry.media_info().video_stream() is not None and entry.duration() in (0,.00, None):

				if entry.source().endswith('.webm'):
					self.logger().info('Processing %s' % entry.source())
					vfile = str(entry.source())
					vfilecopy = str(vfile) + '_copy.webm'

					copystream = ffmpeg.input(vfile)
					copystream = ffmpeg.output(copystream, vfilecopy, vcodec='copy', acodec='copy')

					copystream.global_args(['-loglevel', 'error', '-hide_banner']).run()

					os.rename(vfile, vfile + '.org')
					os.rename(vfilecopy, vfile)

					#if self.args().no_overwrite_missing_meta is True:
					#	os.remove(vfile + '.org')
				else:
					self.logger().error('No copy routine implemented for %s' % entry.source())

		return Command.COMMAND_SUCCESS