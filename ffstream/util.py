import ffmpeg
import pprint

class IntVector2:
	def __init__(self, value: str = None, x: int = None, y: int = None):
		if isinstance(value, str):
			self.parse_str(value)
		elif isinstance(x, int) and isinstance(y, int):
			self.set(x, y)
		else:
			self._x = 0
			self._y = 0

	def set(self, x: int, y: int) -> 'IntVector2':
		if not isinstance(x, int) or not isinstance(y, int):
			raise ValueError

		if x == 0 and y == 0:
			raise ValueError

		self._x = x
		self._y = y
		return self

	def is_valid(self) -> bool:
		return self._x > 0 and self._y > 0

	def x(self) -> int:
		return self._x

	def y(self) -> int:
		return self._y

	def parse_str(self, value: str, delimiter: str = 'x') -> 'IntVector2':
		if not isinstance(value, str):
			raise ValueError

		value = value.lower()

		if delimiter not in value:
			raise ValueError

		parts = value.split(delimiter)

		if not len(parts) == 2:
			raise ValueError

		self.set(int(parts[0]), int(parts[1]))

		return self

"""
Serializable
"""

class Serializable:
	def serialize(self) -> dict:
		return dict()


"""
VideoResolution
"""


class VideoResolution(IntVector2):
	pass


"""
MediaInfo
"""


class MediaInfo:
	def __init__(self, file_path: str = None):
		self._re_init_members()
		if isinstance(file_path, str):
			self.probe(file_path)

	def _re_init_members(self):
		self._video_streams = []
		self._audio_streams = []
		self._was_probed = False
		self._probe_data = False
		self._source = None

	def probe(self, file_path: str, reprobe: bool = False):
		if self._was_probed:
			if reprobe is not True:
				raise MediaInfoError('Already probed, try specifying reprobe')
			else:
				self._re_init_members()

		self._was_probed = True
		self._source = file_path

		try:
			self._probe_data = ffmpeg.probe(file_path)
		except ffmpeg.Error as e:
			raise MediaInfoError('Error probing %s' % file_path)

		for stream in self._probe_data['streams']:
			if stream['codec_type'] == 'video':
				self._video_streams.append(VideoStreamInfo(stream))
			elif stream['codec_type'] == 'audio':
				self._audio_streams.append(AudioStreamInfo(stream))

		if not self.stream_count():
			raise MediaInfoError('No streams in file %s' % self._source)

	def source(self):
		return self._source

	def was_probed(self) -> bool:
		return self._was_probed

	def video_stream(self, index: int = 0) -> 'VideoStreamInfo':
		try:
			return self._video_streams[index]
		except IndexError:
			return None

	def video_streams(self) -> list:
		return self._video_streams

	def video_stream_count(self):
		return len(self.video_streams())

	def audio_stream(self, index: int = 0) -> 'AudioStreamInfo':
		try:
			return self._audio_streams[index]
		except IndexError:
			return None

	def audio_streams(self) -> list:
		return self._audio_streams

	def audio_stream_count(self):
		return len(self.video_streams())

	def stream_count(self):
		return len(self.video_streams()) + len(self.audio_streams())


"""
MediaInfoError
"""


class MediaInfoError(ffmpeg.Error):
	pass


"""
StreamInfo
"""


class StreamInfo:
	def __init__(self, probed_data: dict):
		if not isinstance(probed_data, dict):
			raise ValueError
		self._data = probed_data

	def has(self, field: str):
		return field in self._data

	def get(self, field: str, default=None):
		if field in self._data:
			return self._data[field]
		return default

	def start(self) -> float:
		return float(self.get('start', 0.00))

	def duration(self) -> float:
		if self.has('duration'):
			return float(self.get('duration', 0.00))
		if self.has('tags'):
			tags = self.get('tags', {})
			if 'DURATION' in tags and isinstance(tags['DURATION'], str):
				h, m, s = tags['DURATION'].split(':')
				return float(((int(h) * 60) * 60) + (int(m) * 60) + float(s))
		return None


"""
VideoStreamInfo
"""


class VideoStreamInfo(StreamInfo):
	def resolution(self) -> VideoResolution:
		ret = VideoResolution()
		ret.set(self.get('width'), self.get('height'))
		return ret

"""
AudioStreamInfo
"""


class AudioStreamInfo(StreamInfo):
	pass


"""
TextColor
"""


class TextColor:
	WHITE = '\033[0m'
	RED = '\033[31m'
	GREEN = '\033[32m'
	ORANGE = '\033[33m'
	BLUE = '\033[34m'
	PURPLE = '\033[35m'


class Logger(object):
	def error(self, message):
		raise Exception('Must Implement')

	def info(self, message):
		raise Exception('Must Implement')

	def notice(self, message):
		raise Exception('Must Implement')

	def warning(self, message):
		raise Exception('Must Implement')

	def pprint(self, data, indent: int = 4):
		pprint.PrettyPrinter(indent=indent).pprint(data)


class StdOutLogger(Logger):
	def write(self, message, icon=''):
		if len(icon):
			print('[%s] %s' % (icon, message))
		else:
			print(message)

	def error(self, message):
		self.write(message, 'x')

	def info(self, message):
		self.write(message, '!')

	def notice(self, message):
		self.write(message, '+')

	def warning(self, message):
		self.write(message, '*')
