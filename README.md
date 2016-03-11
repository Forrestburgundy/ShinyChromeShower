# ShinyChromeShower
ShinyChromeShower is a python script which pulls wallpapers and overlays 'ShowerThoughts' from [/r/showerthoughts](www.reddit.com/r/showerthoughts) onto them. These wallpapers are then uploaded to your personal flickr library which allows them to be used as a backdrop on your Chromecast. ShinyChromeShower uses [flickr-uploadr](https://github.com/trickortweak/flickr-uploader) by trickortweak.

##Requirements
* Python 2.7

##Setup
The following python packahes are required to run ShinyChromeShower
* Pillow
* Praw

These are most easily installed using pip. ie `pip install Pillow`. If you do not have pip installed, you can find instructions [here](https://pip.pypa.io/en/stable/installing/).

You will need to create a flickr api key (can be done for free) and add your key and secret into uploadr.ini.

By default, ShinyChromeShower gets the top 10 images from the EarthPorn to overlay onto. You can change this at the top of ShinyChromeShower.py as well as the font used.

## Disclaimer
I'm by no means great at python and simply fiddle in my spare time. If you see something that could be improved, raise an issue or push the fix yourself.

