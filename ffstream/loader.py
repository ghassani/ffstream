import os
import re
import json
from pathlib import Path
from collections import OrderedDict
from .core import Application
from .util import MediaInfo, MediaInfoError
from .playlist import Playlist, PlaylistEntry, PlaylistFilterEntry, PlaylistProfile, PlaylistEntryProfile
from .filter import FilterValidationException
from .ffmpeg import ArgumentContainer as FfmpegArgContainer
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
			json_root = json.load(fp, object_pairs_hook=OrderedDict)
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

				try:
					handler.validate(options)
				except FilterValidationException as e:
					raise PlaylistLoaderError('Filter handler reported invalid option: %s' % e.message())

				playlist.add_filter(PlaylistFilterEntry(handler, options))

		if 'entries' in json_root and isinstance(json_root['entries'], list):
			for i, e in enumerate(json_root['entries'], 0):
				self.application().logger().info('Processing Entry %d - %s' % (i, e['source']))
				try:
					info = MediaInfo(e['source'])
				except MediaInfoError as ex:
					raise PlaylistLoaderError(ex.message(), e)

				entry = PlaylistEntry(info)

				if 'start' in e:
					entry.set_start(float(e['start']))

				if 'duration' in e:
					if e['duration'] in ('', None, 0.00):
						duration = float(info.video_stream().duration())
						self.application().logger().info('Corrected Duration to %f from probed info' % duration)
					else:
						duration = float(e['duration'])
					if info.video_stream_count() > 0:
						check = info.video_stream().duration()
						if check not in (0.00, None) and check != duration:
							duration = check
					entry.set_duration(duration)

				if 'end' in e:
					entry.set_end(float(e['end']))
				else:
					entry.set_end(entry.duration())

				if 'title' in e:
					entry.set_title(e['title'])

				if 'author' in e:
					entry.set_author(e['author'])

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

						try:
							handler.validate(options)
						except FilterValidationException as e:
							raise PlaylistLoaderError('Filter handler reported invalid options for %s - %s' % (handler.name(), e.message()))

						entry.add_filter(PlaylistFilterEntry(handler, options))

				if 'profile' in e and isinstance(e['profile'], dict):
					entry.set_profile(PlaylistEntryProfile(e['profile']))

				playlist.add_entry(entry)

		if 'profile' in json_root and isinstance(json_root['profile'], dict):
			playlist.set_profile(PlaylistProfile(json_root['profile']))

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
