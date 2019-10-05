import pytest
from ffstream.playlist import Playlist, PlaylistEntry, PlaylistOutput, PlaylistProfile, PlaylistEntryProfile, \
								PlaylistFilterEntry, PlaylistQueue

from ffstream.util import MediaInfo, VideoResolution
from ffstream.ffmpeg import ArgumentContainer
from .mock import FilterMock

"""
test_playlist_default
"""


def test_playlist_default():
	playlist = Playlist()

	assert isinstance(playlist.name(), str)
	assert isinstance(playlist.entries(), list)
	assert isinstance(playlist.filters(), list)
	assert isinstance(playlist.output(), PlaylistOutput)
	assert isinstance(playlist.profile(), PlaylistProfile)
	assert isinstance(playlist.should_loop(), bool)
	assert isinstance(playlist.should_shuffle(), bool)
	assert isinstance(playlist.should_loop_shuffle(), bool)


"""
test_playlist_entry_default
"""


def test_playlist_entry_default():
	entry = PlaylistEntry(MediaInfo('tests/data/short.mp4'))

	assert isinstance(entry.title(), str)
	assert isinstance(entry.author(), str)
	assert isinstance(entry.source(), str)
	assert isinstance(entry.start(), float)
	assert isinstance(entry.duration(), float)
	assert isinstance(entry.end(), float)
	assert isinstance(entry.output_duration(), float)
	assert isinstance(entry.filters(), list)
	assert isinstance(entry.has_filters(), bool)
	assert isinstance(entry.profile(), PlaylistEntryProfile)
	assert isinstance(entry.media_info(), MediaInfo)
	assert isinstance(entry.serialize(), dict)

	assert entry.title() == ''
	assert entry.author() == ''
	assert entry.source() == 'tests/data/short.mp4'

	entry.set_title('FOO').set_author('BAR')

	assert entry.title() == 'FOO'
	assert entry.author() == 'BAR'

	entry.set_media_info(MediaInfo('tests/data/medium.mp4'))

	assert isinstance(entry.media_info(), MediaInfo)
	assert entry.source() == 'tests/data/medium.mp4'

	assert not len(entry.filters())
	assert entry.has_filters() is False

	filter = FilterMock({
		'foo': 'bar'
	})

	filter_entry = PlaylistFilterEntry(filter, {
		'bar': 'foo',
		'foo': 'baz'
	})

	entry.add_filter(filter_entry)

	assert len(entry.filters()) == 1
	assert entry.has_filters() is True

	entry.clear_filters()

	assert len(entry.filters()) == 0
	assert entry.has_filters() is False


"""
test_playlist_filter_entry_default
"""


def test_playlist_filter_entry_default():
	filter = FilterMock({
		'foo': 'bar'
	})

	filter_entry = PlaylistFilterEntry(filter, {
		'bar': 'foo',
		'foo': 'baz'
	})

	assert isinstance(filter_entry.handler(), FilterMock)
	assert isinstance(filter_entry.options(), dict)
	assert isinstance(filter_entry.serialize(), dict)

	assert 'bar' in filter_entry.options()
	assert isinstance(filter_entry.options()['bar'], str)
	assert filter_entry.options()['bar'] == 'foo'

	assert 'foo' in filter_entry.options()
	assert isinstance(filter_entry.options()['foo'], str)
	assert filter_entry.options()['foo'] == 'baz'

	assert isinstance(filter_entry.handler().options(), dict)


"""
test_playlist_output_default
"""


def test_playlist_output_default():
	o = PlaylistOutput({
		'destination': 'out.mp4',
		'resolution': '1024x768'
	})

	assert isinstance(o.destination(), str)
	assert isinstance(o.resolution(), VideoResolution)

	assert o.resolution().x() == 1024
	assert o.resolution().y() == 768


"""
test_playlist_profile_default
"""


def test_playlist_profile_default():
	o = PlaylistProfile()

	assert isinstance(o.encoder_args(), ArgumentContainer)
	assert isinstance(o.decoder_args(), ArgumentContainer)

	assert o.encoder_args().has_args() is False
	assert o.decoder_args().has_args() is False

	o = PlaylistProfile({
		'encoder': {
			'global': ['foo', 'bar'],
			'input': {
				'foo': 'bar'
			},
			'output': {
				'bar': 'foo'
			}
		},
		'decoder': {
			'global': ['bin', 'baz'],
			'input': {
				'bin': 'baz'
			},
			'output': {
				'bin': 'baz'
			}
		}
	})

	assert isinstance(o.encoder_args(), ArgumentContainer)
	assert isinstance(o.decoder_args(), ArgumentContainer)

	assert o.encoder_args().has_args() is True
	assert o.decoder_args().has_args() is True

	o = PlaylistProfile({
		'encoder': {
			'global': ['foo', 'bar'],
			'input': {
				'foo': 'bar'
			},
			'output': {
				'bar': 'foo'
			}
		}
	})

	assert o.encoder_args().has_args() is True
	assert o.decoder_args().has_args() is False


"""
test_playlist_entry_profile_default
"""


def test_playlist_entry_profile_default():
	o = PlaylistEntryProfile()

	assert isinstance(o.decoder_args(), ArgumentContainer)

	assert o.decoder_args().has_args() is False

	o = PlaylistProfile({
		'decoder': {
			'global': ['bin', 'baz'],
			'input': {
				'bin': 'baz'
			},
			'output': {
				'bin': 'baz'
			}
		}
	})

	assert isinstance(o.decoder_args(), ArgumentContainer)

	assert o.decoder_args().has_args() is True




"""
test_playlist_queue_default
"""


def test_playlist_queue_default():

	playlist = Playlist()
	playlist.add_entry(PlaylistEntry(MediaInfo('tests/data/short.mp4')))
	playlist.add_entry(PlaylistEntry(MediaInfo('tests/data/medium.mp4')))

	queue = PlaylistQueue(playlist)

	assert queue.current() is None
	assert isinstance(queue.peek_next(), PlaylistEntry)
	assert queue.peek_last() is None
	assert queue.count() == 2
	assert queue.peek_next().source() == 'tests/data/short.mp4'

	queue.next()  # move iterator

	assert isinstance(queue.current(), PlaylistEntry)
	assert isinstance(queue.peek_next(), PlaylistEntry)
	assert queue.peek_last() is None
	assert queue.current().source() == 'tests/data/short.mp4'
	assert queue.peek_next().source() == 'tests/data/medium.mp4'

	assert queue.count() == 1

	queue.next()  # move iterator

	assert isinstance(queue.current(), PlaylistEntry)
	assert queue.peek_next() is None
	assert isinstance(queue.peek_last(), PlaylistEntry)

	assert queue.current().source() == 'tests/data/medium.mp4'
	assert queue.peek_last().source() == 'tests/data/short.mp4'

	assert queue.count() == 0

	queue.next()  # move iterator

	assert queue.current() is None
	assert queue.peek_next() is None
	assert isinstance(queue.peek_last(), PlaylistEntry)

	queue.reload_complete()

	assert queue.count() == 2

	assert queue.queue()[0].source() == 'tests/data/short.mp4'
	assert queue.queue()[1].source() == 'tests/data/medium.mp4'


"""
test_playlist_queue_loop
"""


def test_playlist_queue_loop():
	playlist = Playlist()
	playlist.add_entry(PlaylistEntry(MediaInfo('tests/data/short.mp4')))
	playlist.add_entry(PlaylistEntry(MediaInfo('tests/data/medium.mp4')))
	playlist.add_entry(PlaylistEntry(MediaInfo('tests/data/short.mp4')))
	playlist.set_should_loop(True)

	queue = PlaylistQueue(playlist)

	assert queue.queue()[0].source() == 'tests/data/short.mp4'
	assert queue.queue()[1].source() == 'tests/data/medium.mp4'
	assert queue.queue()[2].source() == 'tests/data/short.mp4'

	queue.next()

	assert queue.current().source() == 'tests/data/short.mp4'
	assert queue.queue()[0].source() == 'tests/data/medium.mp4'
	assert queue.queue()[1].source() == 'tests/data/short.mp4'

	queue.next()

	assert queue.current().source() == 'tests/data/medium.mp4'
	assert queue.queue()[0].source() == 'tests/data/short.mp4'
	assert queue.complete_queue()[0].source() == 'tests/data/short.mp4'

	queue.next()

	assert queue.current().source() == 'tests/data/short.mp4'
	assert len(queue.queue()) == 0
	assert len(queue.complete_queue()) == 2
	assert queue.complete_queue()[1].source() == 'tests/data/short.mp4'
	assert queue.complete_queue()[0].source() == 'tests/data/medium.mp4'

	queue.next()

	assert queue.current().source() == 'tests/data/short.mp4'
	assert queue.queue()[0].source() == 'tests/data/medium.mp4'
	assert queue.queue()[1].source() == 'tests/data/short.mp4'

