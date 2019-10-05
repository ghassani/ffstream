from ffstream.filter import Filter
from ffstream.playlist import Playlist, PlaylistEntry
from ffstream.util import MediaInfo
from ffmpeg.nodes import Node


class FilterMock(Filter):

	def name(self) -> str:
		return 'mock_filter'

	def validate(self, options: dict):
		return True

	def preload(self, playlist: Playlist, entry: PlaylistEntry):
		pass

	def apply(self, playlist: Playlist, entry: PlaylistEntry, video: Node, audio: Node, apply_options: dict) -> [Node, Node]:
		return video, audio
