import ffmpeg
from ffmpeg.nodes import Node
from PIL import Image, ImageDraw

"""
Filter
"""


class Filter:
	def __init__(self, options: dict = None):
		self.options = dict()
		if isinstance(options, dict):
			self.options.update(options)

	def name(self) -> str:
		raise Exception('Must be implemented by inheritor')

	def is_valid(self, options: dict) -> bool:
		return True

	def preload(self, playlist: 'Playlist', entry: 'PlaylistEntry'):
		raise Exception('Must be implemented by inheritor')

	def apply(self, playlist: 'Playlist', entry: 'PlaylistEntry', video: Node, audio: Node, apply_options: dict) -> (Node, Node):
		raise Exception('Must be implemented by inheritor')


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

	def get(self, name: str) -> Filter:
		for f in self._filters:
			if f.name() == name:
				return f
		return None


"""
IntervalTextFilter - Adds a text to the video in configurable intervals
"""


class IntervalTextFilter(Filter):
	def name(self):
		return 'interval_text'

	def is_valid(self, options: dict) -> bool:
		if not isinstance(options, dict):
			return False

		if 'text' not in options or not isinstance(options['text'], (str, list)):
			return False

		if 'duration' not in options:
			return False

		if 'interval' not in options:
			return False

		if 'kwargs' in options and not isinstance(options['kwargs'], dict):
			return False

		return True

	def apply(self, playlist: 'Playlist',playlist_entry: 'PlaylistEntry', video: Node, audio: Node, options: dict) -> (Node, Node):
		video_duration = playlist_entry.get_output_duration()
		duration = int(options['duration'])
		interval = int(options['interval'])

		kwargs = options['kwargs'] if 'kwargs' in options else {}

		'''
			if(
				eq(t, 1),
				1,
				eq(mod(t, 20), 0)
			)
		'''

		kwargs['enable'] = 'gt(mod(t,%d), %d)' % (interval, duration)
		kwargs['enable'] = 'if (eq(t, 1), 1, lt(mod(t, 20), 10))'

		video = video.drawtext(options['text'], **kwargs)

		return video, audio


"""
ImageOverlayFilter
"""


class ImageOverlayFilter(Filter):
	def name(self):
		return 'image_overlay'

	def is_valid(self, options: dict) -> bool:
		if not isinstance(options, dict):
			return False

		if 'image' not in options or not isinstance(options['image'], str):
			return False

		if 'kwargs' in options and not isinstance(options['kwargs'], dict):
			return False

		return True

	def apply(self, playlist: 'Playlist', playlist_entry: 'PlaylistEntry', video: Node, audio: Node, options: dict) -> (Node, Node):
		overlay_image = ffmpeg.input(options['image'])
		kwargs = options['kwargs'] if 'kwargs' in options else {}

		video = video.overlay(overlay_image, **kwargs)

		return video, audio


"""
VideoInformationFilter - Adds information to the video as an overlay
"""


class VideoInformationFilter(Filter):
	def name(self):
		return 'video_info'

	def is_valid(self, options: dict) -> bool:
		if not isinstance(options, dict):
			return False

		if 'title' not in options or not isinstance(options['title'], (str, list)):
			return False

		if 'duration' not in options:
			return False

		if 'interval' not in options:
			return False

		if 'kwargs' in options and not isinstance(options['kwargs'], dict):
			return False

		return True

	def apply(self, playlist: 'Playlist',playlist_entry: 'PlaylistEntry', video: Node, audio: Node, options: dict) -> (Node, Node):
		video_duration = playlist_entry.get_output_duration()
		duration = int(options['duration'])
		interval = int(options['interval'])

		kwargs = options['kwargs'] if 'kwargs' in options else {}
		resolution = playlist.output().resolution()

		i = Image.new('RGBA', (resolution.x(), resolution.y()), (255, 0, 0, 0))
		d = ImageDraw.Draw(i).text((0, 0), options['title'], fill=(255,255,0))

		for i in range(0, int(video_duration), interval):
			thiskwargs = kwargs.copy()
			thiskwargs.update({
				'enable': 'between(t,%d,%d)' % (i, i+duration)
			})

			if isinstance(options['text'], list):
				start_x = thiskwargs['x'] if 'x' in thiskwargs else 0
				start_y = thiskwargs['y'] if 'y' in thiskwargs else 0
				inc = int(thiskwargs['fontsize']) if 'fontsize' in thiskwargs else 16

				if 'box' in thiskwargs:
					inc = inc + ( int(thiskwargs['box']) * 2)

				y = start_y
				for line in options['text']:
					line = str(line)
					thiskwargs['y'] = y
					video = video.drawtext(line, **thiskwargs)
					y = y + inc
			else:
				video = video.drawtext(options['text'], **thiskwargs)

		return video, audio
