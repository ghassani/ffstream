import random
from .filter import Filter
from .util import MediaInfo, VideoResolution, Serializable

"""
FfmpegArgContainer
"""


class FfmpegArgContainer(Serializable):
	def __init__(self, data: dict = None):
		self._global = []
		self._output = {}

		if isinstance(data, dict):
			if 'global' in data and isinstance(data['global'], list):
				self._global = data['global']
			if 'output' in data and isinstance(data['output'], dict):
				self._output = data['output']

	def global_args(self) -> list:
		return self._global

	def output_args(self) -> dict:
		return self._output

	def serialize(self) -> dict:
		return {
			'global': self.global_args(),
			'output': self.output_args()
		}


"""
PlaylistEntry
"""


class PlaylistEntry(Serializable):
	def __init__(self, media_info: MediaInfo):
		self._media_info = media_info
		self._start = 0.00
		self._end = 0.00
		self._duration = 0.00
		self._filters = []
		self._decoder_args = FfmpegArgContainer()

		if isinstance(media_info, MediaInfo):
			if media_info.video_stream() is not None:
				self._start = media_info.video_stream().start()
				self._end = media_info.video_stream().duration()
				self._duration = media_info.video_stream().duration()

	def set_media_info(self, media_info: MediaInfo) -> 'PlaylistEntry':
		self._media_info = media_info
		return self

	def media_info(self) -> MediaInfo:
		return self._media_info

	def source(self) -> str:
		return self._media_info.source()

	def set_start(self, start: float) -> 'PlaylistEntry':
		self._start = start
		return self

	def start(self) -> float:
		return self._start

	def set_end(self, e: float) -> 'PlaylistEntry':
		self._end = e
		return self

	def end(self) -> float:
		return self._end

	def set_duration(self, duration: float) -> 'PlaylistEntry':
		self._duration = duration
		return self

	def duration(self) -> float:
		return self._duration

	def filters(self) -> list:
		return self._filters

	def get_output_duration(self) -> float:
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

	def decoder_args(self) -> FfmpegArgContainer:
		return self._decoder_args

	def set_decoder_args(self, args: FfmpegArgContainer) -> 'PlaylistEntry':
		if not isinstance(args, FfmpegArgContainer):
			raise PlaylistError('Expected instance of FfmpegArgContainer')
		self._decoder_args = args
		return self

	def serialize(self) -> dict:
		result = {
			'source': self.source(),
			'start': self.start(),
			'end': self.end(),
			'duration': self.duration(),
			'filters': [],
			'decoder': self.decoder_args().serialize()
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
		self._data = {}
		if isinstance(data, dict):
			self._data = data

		self._destination = self._data['destination'] if 'destination' in self._data else ''
		self._resolution = VideoResolution(self._data['resolution'] if 'resolution' in self._data else None)

	def resolution(self) -> VideoResolution:
		return self._resolution

	def destination(self) -> str:
		return self._destination

	def set_destination(self, destination: str):
		if not isinstance(destination, str):
			raise ValueError
		self._destination = destination
		return self

	def serialize(self) -> dict:
		return {
			'destination': self.destination(),
			'resolution': '%dx%d' % (self.resolution().x(), self.resolution().y())
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
		self._encoder_args = FfmpegArgContainer()
		self._decoder_args = FfmpegArgContainer()
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

	def encoder_args(self) -> FfmpegArgContainer:
		return self._encoder_args

	def set_encoder_args(self, args: FfmpegArgContainer) -> 'Playlist':
		if not isinstance(args, FfmpegArgContainer):
			raise PlaylistError('Expected instance of FfmpegArgContainer')
		self._encoder_args = args
		return self

	def decoder_args(self) -> FfmpegArgContainer:
		return self._decoder_args

	def set_decoder_args(self, args: FfmpegArgContainer) -> 'Playlist':
		if not isinstance(args, FfmpegArgContainer):
			raise PlaylistError('Expected instance of FfmpegArgContainer')
		self._decoder_args = args
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
			'encoder': self.encoder_args().serialize(),
			'decoder': self.decoder_args().serialize(),
			'filters': [],
			'entries': []
		}

		for f in self.filters():
			result['filters'].append(f.serialize())

		for e in self.entries():
			result['entries'].append(e.serialize())

		return result


class PlaylistError(Exception):
	def __init__(self, message: str = '', other: Exception = None):
		self._message = message
		self._other = other

	def message(self) -> str:
		return self._message

	def other(self) -> Exception:
		return self._other