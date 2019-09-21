import os
import re
import json
from pathlib import Path

from .core import Application
from .util import MediaInfo, MediaInfoError
from .playlist import Playlist, PlaylistEntry, PlaylistFilterEntry, FfmpegArgContainer

"""
PlaylistLoader
"""


class PlaylistLoader:
	def __init__(self, application: Application):
		if not isinstance(application, Application):
			raise PlaylistLoaderError('Expected instance of Application')
		self._application = application

	def application(self) -> Application:
		return self._application

	def load(self, path: str, options: dict = None) -> Playlist:
		raise Exception('Must be implemented by inherited class')


"""
DirectoryPlaylistLoader
"""


class DirectoryPlaylistLoader(PlaylistLoader):
	DEFAULT_LOAD_TYPES = ['mp4', 'webm', 'mkv']

	def load(self, directory: str, options: dict = None) -> Playlist:
		recursive = options['recursive'] if 'recursive' in options and isinstance(options['recursive'], bool) else False
		types = options['types'] if 'types' in options and isinstance(options['types'], list) else DirectoryPlaylistLoader.DEFAULT_LOAD_TYPES

		path = Path(directory)

		if not path.is_dir():
			raise PlaylistLoaderError('Playlist path %s is not a file' % path)

		pattern = '**/*' if recursive is True else '*'

		playlist = Playlist()

		for file in path.glob(pattern):
			if file.is_file():
				if re.search('\.(%s)$' % '|'.join(types), file.name):
					try:
						info = MediaInfo(str(file))
					except MediaInfoError:
						continue
					entry = PlaylistEntry(info)
					playlist.add_entry(entry)
		return playlist


"""
JsonPlaylistLoader
"""


class JsonPlaylistLoader(PlaylistLoader):
	def load(self, path: str, options: dict = None) -> Playlist:
		if not os.path.isfile(path):
			raise PlaylistLoaderError('Playlist path %s is not a file' % path)

		try:
			fp = open(path, 'r')
			json_root = json.load(fp)
			fp.close()
		except:
			# TODO: catch specifics
			raise PlaylistLoaderError('Unable to load json file')

		playlist = Playlist(path)

		if 'output' not in json_root or not isinstance(json_root['output'], dict):
			raise PlaylistLoaderError('Expected a dict for output but got %s' % json_root['output'].__class__)

		playlist.set_name(json_root['name'])
		playlist.output().set_destination(json_root['output']['destination'])
		playlist.output().resolution().parse_str(json_root['output']['resolution'])
		playlist.set_should_shuffle(json_root['shuffle'] if 'shuffle' in json_root else False)
		playlist.set_should_loop(json_root['loop'] if 'loop' in json_root else False)
		playlist.set_should_shuffle(json_root['loop_shuffle'] if 'loop_shuffle' in json_root else False)

		if 'filters' in json_root and isinstance(json_root['filters'], list):
			for f in json_root['filters']:
				if not isinstance(f, dict):
					raise PlaylistLoaderError('Expected dictionary for filter entry')

				if 'type' not in f or not isinstance(f['type'], str):
					raise PlaylistLoaderError('Expected string for filter type')

				handler = self.application().filter_manager().get(f['type'])

				if handler is None:
					raise PlaylistLoaderError('Filter handler %s not found' % f['type'])

				options = {}

				if 'options' in f and isinstance(f['options'], dict):
					options.update(f['options'])

				if not handler.is_valid(options):
					raise PlaylistLoaderError('Filter handler reported invalid options for %s' % handler.name())

				playlist.add_filter(PlaylistFilterEntry(handler, options))

		if 'entries' in json_root and isinstance(json_root['entries'], list):
			for e in json_root['entries']:
				info = MediaInfo(e['source'])
				entry = PlaylistEntry(info)

				if 'start' in e:
					entry.set_start(e['start'])

				if 'duration' in e:
					duration = float(e['duration'])
					if info.video_stream_count() > 0:
						check = info.video_stream().duration()
						if check not in (0.00, None) and check != duration:
							duration = check
					entry.set_duration(duration)

				if 'end' in e:
					entry.set_end(e['end'])
				else:
					entry.set_end(entry.duration())

				if 'filters' in e and isinstance(e['filters'], list):
					for f in e['filters']:
						if not isinstance(f, dict):
							raise PlaylistLoaderError('Expected dictionary for filter entry')

						if 'type' not in f or not isinstance(f['type'], str):
							raise PlaylistLoaderError('Expected string for filter type')

						handler = self.application().filter_manager().get(f['type'])

						if handler is None:
							raise PlaylistLoaderError('Filter handler %s not found' % f['type'])

						options = {}

						if 'options' in f and isinstance(f['options'], dict):
							options.update(f['options'])

						if not handler.is_valid(options):
							raise PlaylistLoaderError('Filter handler reported invalid options for %s' % handler.name())

						entry.add_filter(PlaylistFilterEntry(handler, options))

				if 'decoder' in e and isinstance(e['decoder'], dict):
					entry.set_decoder_args(FfmpegArgContainer(e['decoder']))

				playlist.add_entry(entry)

		if 'encoder' in json_root and isinstance(json_root['encoder'], dict):
			playlist.set_encoder_args(FfmpegArgContainer(json_root['encoder']))

		if 'decoder' in json_root and isinstance(json_root['decoder'], dict):
			playlist.set_decoder_args(FfmpegArgContainer(json_root['decoder']))

		return playlist


"""
PlaylistLoaderError
"""


class PlaylistLoaderError(Exception):
	def __init__(self, message: str = '', other: Exception = None):
		self._message = message
		self._other = other

	def message(self) -> str:
		return self._message

	def other(self) -> Exception:
		return self._other