 # -*- coding: utf-8 -*-
import time, praw, urllib, requests, os
from io import BytesIO
from jinja2 import Environment, FileSystemLoader
import subprocess

#######     SETTINGS        #######
FONT = "Roboto"
FONT_URL = "https://fonts.googleapis.com/css?family=Roboto"
IMAGE_SUBREDDIT = "EarthPorn"
TEXT_SUBREDDIT = "Showerthoughts"
LIM = 10
MIN_RESOLUTION = (1920,1080)
#Tolerence is out of 0 to 100 (Percentage)
ASPECT_TOLERENCE = 50
###################################

reddit = praw.Reddit(user_agent="Chromecast_Showerthoughts")
images = reddit.get_subreddit(IMAGE_SUBREDDIT).get_top(limit=LIM)
thoughts = reddit.get_subreddit(TEXT_SUBREDDIT).get_top(limit=LIM)
env = Environment(loader=FileSystemLoader('templates'))

def get_image_size(url):
    """
    Gets the dimensions of a web image. url must be a direct link to the image,
    currently little support around this. Will timeout if

    Args:
        url (string): The url of the hosted image

    Returns:
        tuple(float, float): (image width, image height)
    """
    data = requests.get(url, timeout=(1, 1)).content
    im = Image.open(BytesIO(data))
    return float(im.size[0]), float(im.size[1])

def verify_image_sizing(img_H, img_W, min_RES, tolerance):
    """
    Verifies if an image is suitable for use by checking the aspect ratio
    and minimum resolution.

    Args:
        img_H (int): Height of image
        img_W (int): Width of image
        min_RES (int): Minimum resolution allowable for use
        tolerance (int): tolerance of image constraints in percentage
    Returns:
        Boolean: True if the image is suitable, false otherwise
    """
    "Set default response"
    verified = False

    "Ensure Tolerance value is within required range (0-100)"
    if tolerance >= 0 and tolerance <= 100:
        tolerance = tolerance / 100.0
    else:
        print """Tolerance entered does not meet requirements, must be a whole
        value between 0-100. Quit script."""
        quit()

    "Load H and W into seperate variables"
    min_RES_W = float(min_RES[0])
    min_RES_H = float(min_RES[1])

    "Get aspect decimal for image being pulled and pixel count"
    img_aspect = float(img_H)/float(img_W)
    img_pixel = img_H*img_W

    "Get high and low for tolerance against aspect ratios"
    req_aspect_min = (min_RES_H/min_RES_W) * ( 1 - tolerance)
    req_aspect_max = (min_RES_H/min_RES_W) * (1 + tolerance)

    "Get minimum pixel count in image"
    req_pixel_min = min_RES_H*min_RES_W

    if (req_aspect_min <= img_aspect and img_aspect <= req_aspect_max
        and img_pixel >= req_pixel_min):
        """Image is within tolerance specified and has more pixels
        then the min stated."""
        verified = True
    return verified

def fill_template_url(template, image_url, text):
    """
    Uses jinja2 to fill a given template with the image and text.

    Args:
        template (string): the html file to edit
        image_url (string): the url for the image to place in the template
        text (string): the text to put in the centre of the image
    """
    template = env.get_template(template)
    output = template.render(font=FONT, font_url=FONT_URL, image=image_url,
        showerthought=text, height=MIN_RESOLUTION[1], width=MIN_RESOLUTION[0])
    with open("temp.html", "wb") as fh:
        fh.write(output)

def capture_template(filename):
    """
    Uses webkit to render the processed html file and saves as an image.

    Returns:
        int: 0 if capture is successful, positive int otherwise
    """
    print (r"wkhtmltopdf\bin\wkhtmltoimage --height " +
    str(MIN_RESOLUTION[1]) + " --width " + str(MIN_RESOLUTION[0]) + " --quality 100"
    + " temp.html " + os.getcwd() + filename)
    return subprocess.call(r"wkhtmltopdf\bin\wkhtmltoimage --height " +
    str(MIN_RESOLUTION[1]) + " --width " + str(MIN_RESOLUTION[0]) + " --quality 100"
    + " temp.html " + os.getcwd() + filename)

if __name__ == "__main__":
    for i in range(LIM):
        image = next(images)
        "Handle a non direct imgur link"
        if "imgur" in image.url and "." not in image.url:
            image.url += ".jpg"
        try:
            W, H = get_image_size(image.url)
        except IOError:
            continue
    if verify_image_sizing(H, W, MIN_RESOLUTION, ASPECT_TOLERENCE) == True:
            "Label image using current date and image in sequence."
            imageName = time.strftime(r"\%d%m%y"+ str(i) + ".jpg")
            thought = next(thoughts).title
            fill_template_url("template.html", image.url, thought)
            capture_template(imageName)
            os.remove("temp.html")

#os.system("uploadr.py")
