#!/usr/bin/env python3

from ffstream.core import Application
from ffstream.generate import GeneratePlaylistCommand
from ffstream.stream import StreamPlaylistCommand
from ffstream.media import FixMediaMetaCommand
from ffstream.filter import IntervalTextFilter, ImageOverlayFilter, VideoInformationFilter


def main():
	try:
		application = Application()

		# Add in commands into the Application
		application.add_command(GeneratePlaylistCommand(application))
		application.add_command(StreamPlaylistCommand(application))
		application.add_command(FixMediaMetaCommand(application))

		# Add in filters to the FilterManager
		application.filter_manager().add(IntervalTextFilter())
		application.filter_manager().add(ImageOverlayFilter())
		application.filter_manager().add(VideoInformationFilter())

		return application.run()
	except KeyboardInterrupt:
		return


if __name__ == '__main__':
	main()
