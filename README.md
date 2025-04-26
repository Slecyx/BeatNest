# BeatNest - What is it, why does it exist

BeatNest is a fully open-source music streaming application, developed to offer a free alternative to proprietary platforms.
With BeatNest, you can:

  -Easily access all your favorite music,

  -Download songs and listen offline,

  -Track how many times and for how long you've listened,

  -Create your own custom playlists,

  -Instantly view song lyrics while listening!

BeatNest aims to provide a free, fast, and enjoyable music experience for everyone.

# BeatNest - Requirements and Installation

In order to run the BeatNest application, you will need to install the following requirements:
1. Python Libraries (with pip)

To install the necessary Python libraries, simply run the following commands in your terminal or command prompt:

*pip install ytmusicapi
*pip install yt-dlp
*pip install python-vlc
*pip install pillow
*pip install requests
*pip install pynput
*pip install lyricsgenius

  -ytmusicapi: Used to fetch music data from YouTube Music API.

  -yt-dlp: Used to download music from YouTube videos.

  -python-vlc: Integrates the VLC media player library with Python.

  -Pillow: Required for image processing.

  -requests: Used for making HTTP requests to fetch data from the internet.

  -pynput: Used for keyboard listening and command management.

  -lyricsgenius: Fetches song lyrics using the Genius API.

2. VLC Player and FFP (VLC for Python)

The VLC media player library needs to be installed on your computer. You can download and install VLC from its official website. Additionally, you should configure the necessary FFP (FFmpeg) support files for VLC’s Python module.

  -VLC Media Player: The application will use VLC for music playback, so make sure VLC is installed on your computer.

  -FFMPEG: Provides audio/video processing support for VLC. This module should be installed along with VLC.

Step-by-Step Installation:

  -Download and Install VLC: Download and install VLC on your computer from the official site.

  -Install Python Libraries: Run the above pip install commands in your terminal to install the required Python libraries.

  -Configure VLC Python Module: If you haven't already, use pip install python-vlc to install the VLC Python module.

  -Run the Application: Once all the steps are completed, you can run the BeatNest application!
