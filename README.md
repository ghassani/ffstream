This is a work in progress.

This was built around the idea of streaming a 24/7 playlist of videos to a remote server, but can also be used to output to the filesystem. It supports programatic filters you can utilize/create and call through modifying a playlist json file allowing for simple filter adjustments to video such as cropping or overlaying text/additional videos. It requires no display device to run and can be used to stream from linux server environments.

requires python 3 and ffmpeg

    git clone https://www.github.com/ghassani/ffstream
    cd ffstream
    pip install -r requirements.txt

# Generate a playlist

    ./ffstream.py generate:playlist -d /path/to/my/videos -o /path/to/output/playlist.json

edit your playlist if needed, adjust output (example to RMTP or to filesystem)

# Play the playlist

    ./ffstream.py stream:playlist -p /path/to/my/playlist.py
