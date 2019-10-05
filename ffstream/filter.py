import ffmpeg
from ffmpeg.nodes import Node
from PIL import Image, ImageDraw

"""
Filter
"""


class Filter:
	def __init__(self, options: dict = None):
		self._options = dict()
		if isinstance(options, dict):
			self._options.update(options)

	def name(self) -> str:
		raise Exception('Must be implemented by inheritor')

	def options(self) -> dict:
		return self._options

	def validate(self, options: dict):
		"""

		:param options:
		:return:
		:raises: FilterValidationException
		"""
		return True

	# TODO: implement this for filters which may require generating assets
	def preload(self, playlist: 'Playlist', entry: 'PlaylistEntry'):
		raise Exception('Must be implemented by inheritor')

	def apply(self, playlist: 'Playlist', entry: 'PlaylistEntry', video: Node, audio: Node, apply_options: dict) -> [Node, Node]:
		raise Exception('Must be implemented by inheritor')

	def validate_position(self, field: str, value):
		if not isinstance(value, dict):
			raise FilterValidationException('Expected a dictionary for %s' % field)
		if 'x' not in value:
			raise FilterValidationException('Expected member x in %s' % field)
		elif not isinstance(value['x'], (int, str)):
			raise FilterValidationException('Expected member x to be as string or integer for %s' % field)

		if 'y' not in value:
			raise FilterValidationException('Expected member y in %s' % field)
		elif not isinstance(value['y'], (int, str)):
			raise FilterValidationException('Expected member y to be as string or integer for %s' % field)


"""
FilterManager
"""


class FilterManager:
	def __init__(self):
		self._filters = []

	def filters(self) -> list:
		return self._filters

	def add(self, f: Filter):
		if isinstance(f, Filter):
			self._filters.append(f)
		return self

	def has(self, name: str) -> bool:
		for f in self._filters:
			if f.name() == name:
				return True
		return False

	def get(self, name: str) -> (Filter, None):
		for f in self._filters:
			if f.name() == name:
				return f
		return None


"""
ContinuousTextFilter - Adds a text to the video for the whole duration
"""


class ContinuousTextFilter(Filter):
	def name(self):
		return 'continuous_text'

	def validate(self, options: dict):
		if 'text' not in options or not isinstance(options['text'], str):
			raise FilterValidationException('Expected a string for text')

		if 'kwargs' in options and not isinstance(options['kwargs'], dict):
			raise FilterValidationException('Expected instance of dictionary for kwargs')

	def apply(self, playlist: 'Playlist', playlist_entry: 'PlaylistEntry', video: Node, audio: Node, options: dict) -> [Node, Node]:
		kwargs = options['kwargs'] if 'kwargs' in options else {}

		video = video.drawtext(options['text'], **kwargs)

		return video, audio


"""
IntervalTextFilter - Adds a text to the video in configurable intervals
"""


class IntervalTextFilter(Filter):
	def name(self):
		return 'interval_text'

	def validate(self, options: dict):
		if not isinstance(options, dict):
			raise FilterValidationException('Expected options to be a dictionary')

		if 'text' not in options or not isinstance(options['text'], str):
			raise FilterValidationException('Expected a string for text')

		if 'duration' not in options or not isinstance(options['duration'], (int, float, str)):
			raise FilterValidationException('Expected a float or int for duration')
		else:
			options['duration'] = float(options['duration'])

		if 'interval' not in options or not isinstance(options['duration'], (int, float)):
			if isinstance(options['duration'], int):
				options['duration'] = float(options['duration'])
			raise FilterValidationException('Expected a float or int for duration')

		if 'fallback_divisor' in options:
			if not isinstance(options['fallback_divisor'], int):
				raise FilterValidationException('Expected instance of int for fallback_divisor')
		else:
			options['fallback_divisor'] = 2

		if 'kwargs' in options and not isinstance(options['kwargs'], dict):
			raise FilterValidationException('Expected instance of dictionary for kwargs')

	def apply(self, playlist: 'Playlist', playlist_entry: 'PlaylistEntry', video: Node, audio: Node, options: dict) -> [Node, Node]:
		video_duration = playlist_entry.output_duration()
		duration = int(options['duration'])
		interval = int(options['interval'])

		if interval > video_duration and options['fallback_divisor'] > 0:
			interval = int(video_duration / options['fallback_divisor'])

		kwargs = options['kwargs'] if 'kwargs' in options else {}

		kwargs['enable'] = 'if ( between( t, 0, %d ), 1, lte( mod( t, %d ), %d) )' % (duration, interval, duration)

		video = video.drawtext(options['text'], **kwargs)

		return video, audio


"""
ImageOverlayFilter
"""


class ImageOverlayFilter(Filter):
	def name(self):
		return 'image_overlay'

	def validate(self, options: dict) -> bool:
		if not isinstance(options, dict):
			raise FilterValidationException('Expected dict for options')

		if 'image' not in options or not isinstance(options['image'], str):
			raise FilterValidationException('Expected string for image')

		if 'kwargs' in options and not isinstance(options['kwargs'], dict):
			raise FilterValidationException('Expected dict for kwargs')

		return True

	def apply(self, playlist: 'Playlist', playlist_entry: 'PlaylistEntry', video: Node, audio: Node, options: dict) -> [Node, Node]:
		kwargs = options['kwargs'] if 'kwargs' in options else {}

		if 'animated' in options and options['animated'] is True:
			kwargs['shortest'] = ''
			overlay_image = ffmpeg.input(options['image'])
		else:
			overlay_image = ffmpeg.input(options['image'])

		video = video.overlay(overlay_image, **kwargs)

		return video, audio


"""
VideoInformationFilter - Adds information to the video as an overlay
"""


class VideoInformationFilter(Filter):
	def name(self):
		return 'video_info'

	def validate(self, options: dict) -> bool:
		if not isinstance(options, dict):
			return False

		if 'duration' not in options or not isinstance(options['duration'], (int, float, str)):
			raise FilterValidationException('Expected a float or int for duration')
		else:
			options['duration'] = float(options['duration'])

		if 'interval' not in options or not isinstance(options['duration'], (int, float)):
			if isinstance(options['duration'], int):
				options['duration'] = float(options['duration'])
			raise FilterValidationException('Expected a float or int for duration')

		if 'title_position' in options:
			self.validate_position('', options['title_position'])
		else:
			options['title_position'] = dict(x=0, y=0)

		if 'author_position' in options:
			self.validate_position('author_position', options['author_position'])
		else:
			options['author_position'] = dict(x=0, y=80)

		if 'fallback_divisor' in options:
			if not isinstance(options['fallback_divisor'], int):
				raise FilterValidationException('Expected instance of int for fallback_divisor')
		else:
			options['fallback_divisor'] = 2

		if 'kwargs' in options and not isinstance(options['kwargs'], dict):
			raise FilterValidationException('Expected instance of dictionary for kwargs')

		return True

	def apply(self, playlist: 'Playlist',playlist_entry: 'PlaylistEntry', video: Node, audio: Node, options: dict) -> [Node, Node]:
		video_duration = playlist_entry.output_duration()
		duration = int(options['duration'])
		interval = int(options['interval'])
		title = playlist_entry.title()
		author = playlist_entry.author()

		if interval > video_duration and options['fallback_divisor'] > 0:
			interval = int(video_duration / options['fallback_divisor'])

		kwargs = options['kwargs'] if 'kwargs' in options else {}

		kwargs['enable'] = 'if( between( t, 0, %d ), 1, lte( mod( t, %d ), %d) )' % (duration, interval, duration)
		kwargs['x'] = options['title_position']['x']
		kwargs['y'] = options['title_position']['y']

		# draw title
		if title not in (None, ''):
			video = video.drawtext('Currently Watching: %s' % title if title not in (None, '') else 'Untitled', **kwargs)

		# draw author
		if author not in (None, ''):
			kwargs['x'] = options['author_position']['x']
			kwargs['y'] = options['author_position']['y']

			video = video.drawtext('By: %s' % author, **kwargs)

		return video, audio


class FilterValidationException(Exception):
	def __init__(self, message: str):
		if isinstance(message, str):
			self._message = message

	def message(self) -> str:
		return self._message