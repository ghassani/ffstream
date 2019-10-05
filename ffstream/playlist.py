import random
from .filter import Filter
from .util import MediaInfo, VideoResolution, Serializable
from .ffmpeg import ArgumentContainer as FfmpegArgContainer
from collections import deque
import urllib.parse

"""
PlaylistEntry
"""


class PlaylistEntry(Serializable):
	def __init__(self, media_info: MediaInfo):
		self._media_info = media_info
		self._title = ''
		self._author = ''
		self._start = 0.00
		self._end = 0.00
		self._duration = 0.00
		self._filters = []
		self._profile = PlaylistEntryProfile()

		if not isinstance(media_info, MediaInfo):
			raise TypeError

		if media_info.video_stream() is not None:
			self._start = media_info.video_stream().start()
			self._end = media_info.video_stream().duration()
			self._duration = media_info.video_stream().duration()

	def set_media_info(self, media_info: MediaInfo) -> 'PlaylistEntry':
		self._media_info = media_info
		return self

	def media_info(self) -> MediaInfo:
		return self._media_info

	def title(self) -> str:
		return self._title

	def set_title(self, title: str) -> 'PlaylistEntry':
		if not isinstance(title, str):
			raise ValueError
		self._title = title
		return self

	def author(self) -> str:
		return self._author

	def set_author(self, author: str) -> 'PlaylistEntry':
		if not isinstance(author, str):
			raise ValueError
		self._author = author
		return self

	def source(self) -> str:
		return self._media_info.source()

	def set_start(self, start: float) -> 'PlaylistEntry':
		self._start = start if isinstance(start, float) else float(start)
		return self

	def start(self) -> float:
		return self._start

	def set_end(self, end: float) -> 'PlaylistEntry':
		self._end = end if isinstance(end, float) else float(end)
		return self

	def end(self) -> float:
		return self._end

	def set_duration(self, duration: float) -> 'PlaylistEntry':
		self._duration = duration if isinstance(duration, float) else float(duration)
		return self

	def duration(self) -> float:
		return self._duration

	def filters(self) -> list:
		return self._filters

	def output_duration(self) -> float:
		if self.start() in (0, None):
			return self.end()
		return self.end() - self.start()

	def add_filter(self, f: 'PlaylistFilterEntry') -> 'PlaylistEntry':
		if isinstance(f, PlaylistFilterEntry):
			self._filters.append(f)
		else:
			raise PlaylistError('Expected an instance of PlaylistFilterEntry')
		return self

	def set_filters(self, filters: list) -> 'PlaylistEntry':
		if isinstance(filters, list):
			self.clear_filters()
			for f in filters:
				self.add_filter(f)
		else:
			raise PlaylistError('Expected a list of Filter instances')
		return self

	def has_filters(self) -> bool:
		return len(self._filters) > 0

	def clear_filters(self) -> 'PlaylistEntry':
		self._filters.clear()
		return self

	def profile(self) -> 'PlaylistEntryProfile':
		return self._profile

	def set_profile(self, profile: 'PlaylistEntryProfile') -> 'PlaylistEntry':
		if not isinstance(profile, PlaylistEntryProfile):
			raise PlaylistError('Expected instance of PlaylistEntryProfile')
		self._profile = profile
		return self

	def serialize(self) -> dict:
		result = {
			'title': self.title(),
			'author': self.author(),
			'source': self.source(),
			'start': self.start(),
			'end': self.end(),
			'duration': self.duration(),
			'filters': [],
			'profile': self.profile().serialize()
		}

		for f in self._filters:
			result['filters'].append(f.serialize())

		return result


"""
PlaylistFilterEntry
"""


class PlaylistFilterEntry(Serializable):
	def __init__(self, handler: Filter, options: dict = None):
		self._handler = handler
		self._options = {}
		if isinstance(options, dict):
			self._options.update(options)

	def handler(self) -> Filter:
		return self._handler

	def options(self) -> dict:
		return self._options

	def serialize(self) -> dict:
		return {
			'type': self._handler.name(),
			'options': self.options()
		}


"""
PlaylistOutput
"""


class PlaylistOutput(Serializable):
	def __init__(self, data: dict = None):
		self._destination = ''
		self._resolution = VideoResolution()

		self._data = {}
		if isinstance(data, dict):
			self._data = data

		self.set_destination(self._data['destination'] if 'destination' in self._data else '')
		if 'resolution' in self._data:
			self.set_resolution(self._data['resolution'])

	def resolution(self) -> VideoResolution:
		return self._resolution

	def destination(self) -> str:
		return self._destination

	def set_destination(self, destination: str):
		if not isinstance(destination, str):
			raise ValueError
		self._destination = destination
		return self

	def set_resolution(self, resolution):
		if isinstance(resolution, VideoResolution):
			self._resolution = resolution
		elif isinstance(resolution, str):
			self._resolution.parse_str(resolution)

	def serialize(self) -> dict:
		return {
			'destination': self.destination(),
			'resolution': '%dx%d' % (int(self.resolution().x()), int(self.resolution().y()))
		}


"""
PlaylistProfile
"""


class PlaylistProfile(Serializable):
	def __init__(self, data: dict = None):
		self._encoder_args = FfmpegArgContainer()
		self._decoder_args = FfmpegArgContainer()

		if isinstance(data, dict):
			if 'encoder' in data and isinstance(data['encoder'], dict):
				self._encoder_args = FfmpegArgContainer(data['encoder'])
			if 'decoder' in data and isinstance(data['decoder'], dict):
				self._decoder_args = FfmpegArgContainer(data['decoder'])

	def encoder_args(self) -> FfmpegArgContainer:
		return self._encoder_args

	def set_encoder_args(self, args: FfmpegArgContainer) -> 'PlaylistProfile':
		if not isinstance(args, FfmpegArgContainer):
			raise PlaylistError('Expected instance of FfmpegArgContainer')
		self._encoder_args = args
		return self

	def decoder_args(self) -> FfmpegArgContainer:
		return self._decoder_args

	def set_decoder_args(self, args: FfmpegArgContainer) -> 'PlaylistProfile':
		if not isinstance(args, FfmpegArgContainer):
			raise PlaylistError('Expected instance of FfmpegArgContainer')
		self._decoder_args = args
		return self

	def serialize(self) -> dict:
		return {
			'encoder': self.encoder_args().serialize(),
			'decoder': self.decoder_args().serialize(),
		}


"""
PlaylistEntryProfile
"""


class PlaylistEntryProfile(Serializable):
	def __init__(self, data: dict = None):
		self._decoder_args = FfmpegArgContainer()

		if isinstance(data, dict):
			if 'decoder' in data and isinstance(data['decoder'], dict):
				self._decoder_args = FfmpegArgContainer(data['decoder'])

	def decoder_args(self) -> FfmpegArgContainer:
		return self._decoder_args

	def set_decoder_args(self, args: FfmpegArgContainer) -> 'PlaylistEntryProfile':
		if not isinstance(args, FfmpegArgContainer):
			raise PlaylistError('Expected instance of FfmpegArgContainer')
		self._decoder_args = args
		return self

	def serialize(self) -> dict:
		return {
			'decoder': self.decoder_args().serialize(),
		}


"""
Playlist
"""


class Playlist(Serializable):
	def __init__(self, path: str = None):
		self._name = 'My Playlist'
		self._path = path
		self._entries = []
		self._filters = []
		self._output = PlaylistOutput()
		self._profile = PlaylistProfile()
		self._shuffle = False
		self._loop = False
		self._loop_shuffle = False

	def name(self) -> str:
		return self._name

	def set_name(self, name: str) -> 'Playlist':
		self._name = name
		return self

	def path(self) -> str:
		return self._path

	def set_path(self, path: str) -> 'Playlist':
		self._path = path
		return self

	def entries(self) -> list:
		return self._entries

	def add_entry(self, e: PlaylistEntry) -> 'Playlist':
		if not isinstance(e, PlaylistEntry):
			raise PlaylistError('Expected an instance of PlaylistEntry')
		self.entries().append(e)
		return self

	def entry_count(self) -> int:
		return len(self.entries())

	def shuffle(self):
		random.shuffle(self._entries)

	def filters(self) -> list:
		return self._filters

	def add_filter(self, f: PlaylistFilterEntry) -> 'Playlist':
		if not isinstance(f, PlaylistFilterEntry):
			raise PlaylistError('Expected an instance of PlaylistFilterEntry')
		self.filters().append(f)
		return self

	def has_filters(self) -> bool:
		return len(self._filters) > 0

	def output(self) -> PlaylistOutput:
		return self._output

	def set_output(self, output: PlaylistOutput) -> 'Playlist':
		if not isinstance(output, PlaylistOutput):
			raise PlaylistError('Expected instance of PlaylistOutput')
		self._output = output
		return self

	def profile(self) -> PlaylistProfile:
		return self._profile

	def set_profile(self, profile: PlaylistProfile) -> 'Playlist':
		if not isinstance(profile, PlaylistProfile):
			raise PlaylistError('Expected instance of PlaylistProfile')
		self._profile = profile
		return self

	def should_shuffle(self) -> bool:
		return self._shuffle

	def set_should_shuffle(self, shuffle: bool) -> 'Playlist':
		self._shuffle = shuffle if isinstance(shuffle, bool) else False
		return self

	def should_loop(self) -> bool:
		return self._loop

	def set_should_loop(self, loop: bool) -> 'Playlist':
		self._loop = loop if isinstance(loop, bool) else False
		return self

	def should_loop_shuffle(self) -> bool:
		return self._loop_shuffle

	def set_should_loop_shuffle(self, loop_shuffle: bool) -> 'Playlist':
		self._loop_shuffle = loop_shuffle if isinstance(loop_shuffle, bool) else False
		return self

	def serialize(self) -> dict:
		result = {
			'name': self.name(),
			'shuffle': self.should_shuffle(),
			'loop': self.should_loop(),
			'loop_shuffle': self.should_loop_shuffle(),
			'output': self.output().serialize(),
			'profile': self.profile().serialize(),
			'filters': [],
			'entries': [],
		}

		for f in self.filters():
			result['filters'].append(f.serialize())

		for e in self.entries():
			result['entries'].append(e.serialize())

		return result



"""
PlaylistQueue
"""


class PlaylistQueue:
	def __init__(self, playlist: Playlist):
		if not isinstance(playlist, Playlist):
			raise TypeError
		self._playlist = playlist
		self._queue = deque()
		self._complete_queue = deque()
		self._current = None  # type: (PlaylistEntry, None)
		for entry in playlist.entries():
			self.push_front(entry)

	def total(self) -> int:
		return len(self._queue) + len(self._complete_queue)

	def count(self) -> int:
		return len(self._queue)

	def push_front(self, entry: PlaylistEntry):
		if not isinstance(entry, PlaylistEntry):
			raise TypeError
		self._queue.append(entry)

	def push_back(self, entry: PlaylistEntry):
		if not isinstance(entry, PlaylistEntry):
			raise TypeError
		self._queue.appendleft(entry)

	def push_front_complete(self, entry: PlaylistEntry):
		if not isinstance(entry, PlaylistEntry):
			raise TypeError
		self._complete_queue.append(entry)

	def push_back_complete(self, entry: PlaylistEntry):
		if not isinstance(entry, PlaylistEntry):
			raise TypeError
		self._complete_queue.appendleft(entry)

	def current(self) -> (PlaylistEntry, None):
		"""
		Get the current item to be played
		:return (PlaylistEntry, None):
		"""

		return self._current

	def next(self) -> (PlaylistEntry, None):
		"""
		Move to the next entry in the playlist and return the entry
		:return (PlaylistEntry, None):
		"""
		if isinstance(self._current, PlaylistEntry):
			self.push_back_complete(self._current)

		self._current = None

		if len(self._queue):
			self._current = self._queue.popleft()
		elif len(self._complete_queue) > 0 and self._playlist.should_loop():
			self.reload_complete()
			self._current = self._queue.popleft()

		return self._current

	def last(self) -> (PlaylistEntry, None):
		return self._complete_queue[-1]

	def peek_next(self) -> (PlaylistEntry, None):
		return None if not len(self._queue) else self._queue[0]

	def peek_last(self) -> (PlaylistEntry, None):
		return self._complete_queue[-1] if len(self._complete_queue) else None

	def reload_complete(self):
		if len(self._complete_queue):
			if self._playlist.should_loop() and self._playlist.should_loop_shuffle():
				random.shuffle(self._complete_queue)
			e = self._complete_queue.popleft()
			while e is not None:
				self.push_back(e)
				e = self._complete_queue.popleft() if len(self._complete_queue) else None

	def queue(self) -> deque:
		return self._queue

	def complete_queue(self) -> deque:
		return self._complete_queue

"""
PlaylistQueue
"""


class PlaylistError(Exception):
	def __init__(self, message: str = '', other: Exception = None):
		self._message = message
		self._other = other

	def message(self) -> str:
		return self._message

	def other(self) -> Exception:
		return self._other