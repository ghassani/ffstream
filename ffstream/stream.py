import sys
import ffmpeg
import datetime
import threading
from subprocess import Popen
from io import BufferedReader
from .core import Application, Command, CommandArgumentParser
from .playlist import  Playlist, PlaylistEntry, PlaylistError, PlaylistFilterEntry
from .loader import JsonPlaylistLoader
from .filter import FilterValidationException
from .ffmpeg import ArgumentContainer, Profile


"""
StreamPlaylistCommand
"""


class StreamPlaylistCommand(Command):
	def __init__(self, application: Application, parser: CommandArgumentParser = None):
		super().__init__(application, parser)
		self._playlist = None
		self._encoder = None
		self._decoder = None
		self._encoder_error_buffer = []
		self._encoder_error_thread = None
		self._decoder_error_buffer = []
		self._decoder_error_thread = None

	def name(self):
		return "stream:playlist"

	def description(self):
		return "Start streaming from a json playlist"

	def init(self):
		self.parser().add_argument('-p', '--playlist', help='The playlist to play from', type=str, required=True, default=None)
		self.parser().add_argument('-c', '--check-playlist', help='Just load the playlist, checking for errors', action='store_true', default=False)
		self.set_args(self.parser().parse_args(sys.argv[2:]))

	def encoder(self) -> Popen:
		return self._encoder

	def decoder(self) -> Popen:
		return self._decoder

	def playlist(self) -> Playlist:
		return self._playlist

	def run(self):
		loader = JsonPlaylistLoader(self.application())

		try:
			self._playlist = loader.load(self.args().playlist, {
				'verbose': self.args().verbose
			})

		except PlaylistError as e:
			self.logger().error(e.message())
			return Command.COMMAND_ERROR

		entries = self._playlist.entries().copy()

		# TODO: solve this in Playlist/PlaylistLoader or use another type
		entries.reverse()

		if not len(entries):
			self.logger().error('Nothing in playlist')
			return Command.COMMAND_ERROR

		self.logger().info('Loaded Playlist: %s [%d Entries]' % (self._playlist.path(), self._playlist.entry_count()))

		if self.playlist().should_shuffle() is True:
			self.logger().info('Shuffling Playlist')
			self.playlist().shuffle()

		if self.args().verbose:
			for i, e in enumerate(entries, 1):
				self.logger().info('\t%d) %s [%s - %s | %s]' % (i, e.source(), e.start(), e.end(), e.duration()))

		if self.args().check_playlist is True:
			return Command.COMMAND_SUCCESS

		playlist_profile = self.playlist().profile()
		encoder_args = Profile.ffplayout_encoder()
		encoder_args = Profile.ffplayout_encoder()

		if playlist_profile.encoder_args().has_args():
			encoder_args = playlist_profile.encoder_args()

		resolved_global_args = encoder_args.global_args()
		resolved_input_args = encoder_args.input_args()
		resolved_output_args = encoder_args.output_args()

		if self.args().very_verbose:
			self.logger().info('Encoder Global Args: {}'.format(resolved_global_args))
			self.logger().info('Encoder Input Args: {}'.format(resolved_input_args))
			self.logger().info('Encoder Output Args: {}'.format(resolved_output_args))

		resolved_output_args['metadata:g:0'] = 'service_name=%s' % self.playlist().name()
		resolved_output_args['metadata:g:1'] = 'service_provider=%s/%s' % (self.application().name(), self.application().version())
		resolved_output_args['metadata:g:2'] = 'year=%d' % datetime.datetime.now().year

		for entry in self.playlist().entries():
			decoder_args = Profile.default_decoder()
			entry_profile = entry.profile()

			if entry_profile.decoder_args().has_args():
				decoder_args = entry_profile.decoder_args()
			elif self.playlist().profile().decoder_args().has_args():
				decoder_args = self.playlist().profile().decoder_args()

		encoder_builder = (
			ffmpeg
			.input('pipe:', **resolved_input_args)
			.output(self.playlist().output().destination(), **resolved_output_args)
			.overwrite_output()
			.global_args(*resolved_global_args)
		)

		if self.args().verbose:
			self.logger().info('Encoder Args: {}'.format(' '.join(encoder_builder.compile())))

		self._encoder = encoder_builder.run_async(pipe_stdin=True, pipe_stderr=False)

		if self._encoder.stderr is not None:
			self._encoder_error_thread = threading.Thread(target=self._error_thread, args=(self._encoder.stderr, self._encoder_error_buffer))
			self._encoder_error_thread.daemon = True
			self._encoder_error_thread.start()

		while True:
			if not self._is_encoder_valid():
				error = self._get_encoder_error()
				if error is not None and len(error):
					self.logger().error('Encoder Error: %s' % error)
				else:
					self.logger().error('Encoder Error')
				break

			try:
				entry = entries.pop()
			except IndexError:
				break

			if not self._play_entry(entry):
				if self.playlist().should_loop() is True:
					if self.playlist().should_loop_shuffle() is True:
						self.playlist().shuffle()
					entries = self.playlist().entries().copy()
				else:
					break
			self.encoder().stdin.flush()

		self.encoder().stdin.close()
		self.encoder().terminate()

		return Command.COMMAND_ERROR

	def _play_entry(self, entry: PlaylistEntry):
		self.logger().info('Playing %s' % entry.source())

		if not self._is_encoder_valid():
			self.logger().error('Encoder not valid')
			return False

		probed_video_stream = entry.media_info().video_stream()
		probed_audio_stream = entry.media_info().audio_stream()

		if not probed_video_stream and not probed_audio_stream:
			self.logger().error('No video or audio streams in playlist entry')
			self.encoder().stdin.close()
			self.encoder().wait()
			return False

		if not probed_audio_stream:
			self.logger().error('No audio stream in file %s' % entry.source())
			return False

		decoder_args = Profile.ffplayout_decoder()
		entry_profile = entry.profile()

		if entry_profile.decoder_args().has_args():
			decoder_args = entry_profile.decoder_args()
		elif self.playlist().profile().decoder_args().has_args():
			decoder_args = self.playlist().profile().decoder_args()

		decoder_global_args = decoder_args.global_args()
		decoder_input_args = decoder_args.input_args()
		decoder_output_args = decoder_args.output_args()

		if self.args().very_verbose:
			self.logger().info('Decoder Global Args: {}'.format(decoder_global_args))
			self.logger().info('Decoder Input Args: {}'.format(decoder_input_args))
			self.logger().info('Decoder Output Args: {}'.format(decoder_output_args))

		decoder_builder = ffmpeg.input(entry.source(), **decoder_input_args)

		start = float(entry.start())
		end = float(entry.end())
		duration = float(entry.duration())

		video = None
		audio = None

		if start > 0 or (end != duration and end < duration):
			video = decoder_builder.video.trim(start=start, end=end).setpts('PTS-STARTPTS')

			audio = decoder_builder.audio.filter('atrim', start=start, end=end).filter('asetpts', 'PTS-STARTPTS')
			joined = ffmpeg.concat(video, audio, v=1, a=1).node

			video = joined[0]
			audio = joined[1]
		else:
			video = decoder_builder.video
			audio = decoder_builder.audio

		video = video.filter('scale', self.playlist().output().resolution().x(), self.playlist().output().resolution().y(), force_original_aspect_ratio='1')

		if probed_video_stream.resolution().x() < self.playlist().output().resolution().x():
			video = video.filter('pad', self.playlist().output().resolution().x(), self.playlist().output().resolution().y(), '(ow-iw)/2', '(oh-ih)/2')

		# Apply global filters first

		if self.playlist().has_filters():
			for f in self.playlist().filters():  # type: PlaylistFilterEntry
				video, audio = f.handler().apply(self.playlist(), entry, video, audio, f.options())

		# Apply entry level filters

		if entry.has_filters():
			for f in entry.filters():  # type: PlaylistFilterEntry
				video, audio = f.handler().apply(self.playlist(), entry, video, audio, f.options())

		# Finalize and output

		decoder_builder = ffmpeg.output(video, audio, 'pipe:', **decoder_output_args)
		decoder_builder = decoder_builder.global_args(*decoder_global_args)

		if self.args().verbose:
			self.logger().info('Decoder Args: {}'.format(' '.join(decoder_builder.compile())))

		self._decoder = (
			decoder_builder.run_async(pipe_stdout=True, pipe_stderr=False)
		)

		if self._decoder.stderr is not None:
			self._decoder_error_thread = threading.Thread(target=self._error_thread, args=(self._decoder.stderr, self._decoder_error_buffer))
			self._decoder_error_thread.daemon = True
			self._decoder_error_thread.start()

		while True:
			# TODO see if we can somehow re-encode from here?
			error = self._get_decoder_error()

			if error is not None and len(error):
				print(len(error))
				self.logger().error('Decoder Error: %s' % error)

			buf = self._decoder.stdout.read(16*1024)
			if not buf:
				break
			self._encoder.stdin.write(buf)

		self.decoder().wait()

		return True

	def _is_encoder_valid(self):
		if self._encoder is None:
			return False
		return self._is_process_valid(self._encoder)

	def _get_encoder_error(self):
		# TODO: mutex on buffer?
		ret = None
		if len(self._decoder_error_buffer):
			ret = ''
			for r in self._decoder_error_buffer:
				ret = ret + r.decode('utf8')
			self._decoder_error_buffer.clear()
			return ret
		return ret

	def _stop_encoder(self):
		pass

	def _is_decoder_valid(self):
		if self._decoder is None:
			return False
		return self._is_process_valid(self._decoder)

	def _get_decoder_error(self):
		# TODO: mutex on buffer?
		if len(self._decoder_error_buffer):
			ret = ''
			for r in self._decoder_error_buffer:
				ret = ret + r.decode('utf8')
			self._decoder_error_buffer.clear()
			return ret
		return None

	def _stop_decoder(self):
		pass

	def _is_process_valid(self, process: Popen):
		if not isinstance(process, Popen):
			return False
		if process.poll() is not None:
			return False
		return True

	def _error_thread(self, fh: BufferedReader, buffer: list):  # TODO: move away from list, use a buffered data type
		buffer.append(fh.read())
		fh.flush()
