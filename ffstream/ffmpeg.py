from .util import Serializable
from subprocess import Popen
from collections import OrderedDict
from threading import Thread, Lock


'''
ArgumentContainer
'''


class ArgumentContainer(Serializable):
	def __init__(self, data: dict = None):
		self._global = list()
		self._input = OrderedDict()
		self._output = OrderedDict()

		if isinstance(data, dict):
			if 'global' in data and isinstance(data['global'], list):
				self._global = data['global']
			if 'input' in data and isinstance(data['input'], dict):
				if isinstance(data['output'], OrderedDict):
					self._input = data['input']
				else:
					self._input = OrderedDict(data['input'])
			if 'output' in data and isinstance(data['output'], dict):
				if isinstance(data['output'], OrderedDict):
					self._output = data['output']
				else:
					self._output = OrderedDict(data['output'])

	def global_args(self) -> list:
		return self._global

	def set_global_args(self, args: list) -> 'ArgumentContainer':
		if not isinstance(args, list):
			raise ValueError
		self._global = args
		return self

	def has_global_args(self) -> bool:
		return len(self._global) > 0

	def input_args(self) -> OrderedDict:
		return self._input

	def has_input_args(self) -> bool:
		return len(self._input) > 0

	def set_input_args(self, args: OrderedDict) -> 'ArgumentContainer':
		if not isinstance(args, OrderedDict):
			raise ValueError
		self._input = args
		return self

	def merge_input_args(self, args: OrderedDict) -> 'ArgumentContainer':
		if not isinstance(args, OrderedDict):
			raise ValueError
		self._input.update(args)
		return self

	def output_args(self) -> OrderedDict:
		return self._output

	def set_output_args(self, args: OrderedDict) -> 'ArgumentContainer':
		if not isinstance(args, OrderedDict):
			raise ValueError
		self._output = args
		return self

	def merge_output_args(self, args: OrderedDict) -> 'ArgumentContainer':
		if not isinstance(args, OrderedDict):
			raise ValueError
		self._output.update(args)
		return self

	def has_output_args(self) -> bool:
		return len(self._output) > 0

	def has_args(self) -> bool:
		return self.has_global_args() or self.has_input_args() or self.has_output_args()

	def copy(self) -> 'ArgumentContainer':
		return ArgumentContainer(self.serialize())

	def serialize(self) -> dict:
		return {
			'global': self.global_args(),
			'input': self.input_args(),
			'output': self.output_args()
		}


'''
FfmpegProcessThread
'''


class FfmpegProcessThread:
	def __init__(self, config: ArgumentContainer):
		self._config = config
		self._process = None
		self._started = False
		self._should_stop = False

	def config(self) -> ArgumentContainer:
		return self._config

	def process(self) -> Popen:
		return self._process

	def run(self):
		pass

	def stop(self):
		pass


class EncoderProcessThread(FfmpegProcessThread):
	pass

class DecoderProcessThread(FfmpegProcessThread):
	pass


class Profile:
	@staticmethod
	def default() -> (ArgumentContainer, ArgumentContainer):
		return Profile.default_encoder(), Profile.default_decoder()

	@staticmethod
	def ffplayout() -> (ArgumentContainer, ArgumentContainer):
		return Profile.ffplayout_encoder(), Profile.ffplayout_decoder()

	@staticmethod
	def default_encoder() -> ArgumentContainer:
		return ArgumentContainer({
			'global': ['-loglevel', 'error', '-hide_banner', '-preset', 'high'],
			'input': OrderedDict({
				're': None
			}),
			'output': {
				"c:v": "copy",
				"g": "60",
				"keyint_min": "2",
				"force_key_frames": "expr:gte(t,n_forced*2)",
				"maxrate": "1300k",
				"bufsize": "2600k",
				"preset": "medium",
				"c:a": "copy",
				"bsf:a": "aac_adtstoasc",
				"flags": "+global_header",
				"f": "flv"
			}
		})

	@staticmethod
	def default_decoder() -> ArgumentContainer:
		return ArgumentContainer({
			'global': ['-loglevel', 'error', '-hide_banner', '-preset', 'high'],
			'input': OrderedDict({}),
			'output': OrderedDict({
				"f": "mpegts",
				"pix_fmt": "yuv420p",
				"codec:v": "libx264",
				"g": "60",
				"keyint_min": "2",
				"force_key_frames": "expr:gte(t,n_forced*2)",
				"codec:a": "aac",
				"bufsize": "400k",
				"strict": "experimental",
				"b:v": "800k",
				"b:a": "64k",
				"ar": "44100",
				"maxrate": "800k",
				"profile:v": "Main"
			})
		})

	@staticmethod
	def ffplayout_encoder() -> ArgumentContainer:
		return ArgumentContainer({
			'global': ['-v', 'error', '-hide_banner', '-nostats', '-thread_queue_size', '256'],
			'input': OrderedDict({
				're': None
			}),
			'output': OrderedDict({
				'c:v': 'libx264',
				'crf': '23',
				'x264-params': 'keyint=50:min-keyint=25:scenecut=-1',
				'maxrate': '1300k',
				'bufsize': '2600k',
				'preset': 'medium',
				'profile:v': 'Main',
				'level': '3.1',
				'c:a': 'aac',
				'ar': '44100',
				'b:a': '128k',
				'flags': '+global_header',
				'f': 'flv'
			})
		})

	@staticmethod
	def ffplayout_decoder() -> ArgumentContainer:
		return ArgumentContainer({
			'global': ['-v', 'error', '-hide_banner', '-nostats'],
			'input': OrderedDict({

			}),
			'output': OrderedDict({
				'pix_fmt': 'yuv420p',
				'framerate': '25',
				'c:v': 'mpeg2video',
				'intra': None,
				'b:v': '51200k',
				'minrate': '51200k',
				'maxrate': '51200k',
				'bufsize': '25600.0k',
				'c:a': 's302m',
				'strict': '-2',
				'ar': '48000',
				'ac': '2',
				'f': 'mpegts'
			})
		})
