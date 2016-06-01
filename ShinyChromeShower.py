#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from PIL import Image, ImageDraw, ImageFont, ImageFile
import time, praw, urllib2, math, os
import argparse, ConfigParser

def get_resource_path(relPath):
    """
    Get Resource file from script directory.
    
    Args:
        relPath (string): the path of the relative path
    
    Returns:
        full path of resource file.
    """
    scriptPath = os.path.realpath(__file__)
    scriptdir = os.path.dirname(scriptPath)
    result= os.path.join(scriptdir,relPath)        
    return result
    
def fix_image_url(url):
    """
    Adjust URL according to service standart url structures.
    
    Args:
        url (string): The url of the hosted image
    
    Returns:
        Standartized url string for the image.
    """
    result = url #Default
    
    #Adjust imgur URLs
    if "imgur.com" in url:
        if ".jpg" not in url: 
            result = url +".jpg"
        result = result.replace('http://imgur.com','http://i.imgur.com')

    return result

def get_image_size(url):
    """
    Gets the dimensions of a web image. url must be a direct link to the image,
    currently little support around this. Will timeout if 
    
    Args:
        url (string): The url of the hosted image
    
    Returns:
        tuple(float, float): (image width, image height). 
        on failure: (None, None).
    """
    width = height = None
    try:
        file = urllib2.urlopen(url)
    except: 
        print("urllib2.urlopen failed.",end='')
        return width,height
    try:
        p = ImageFile.Parser()
    except: 
        print("ImageFile.Parser failed.",end='')
        return width,height        
    
    while 1:
        data = file.read(1024)
        if not data:
            print('EOF reached.',end ='')
            break
        p.feed(data)
        if p.image:
            w,h = p.image.size
            width = float(w)
            height = float(h)
            break
    file.close()
    return width,height

def filter_image(post):
    """
    Decide if the image fits this scripts requirements.
        *Resolution above 1080p
        *Aspect ratio between 0.47 to 0.64 (seems to work well)
    
    Args:
        post: a single praw post object
    
    Returns:
        Boolean of validity
    """
    #require a minimum of 1080p.
    MIN_RESOLUTION = 1920*1080
    #Arbitrary threshold for aspect ratio.
    MIN_ASPECT_RATIO = 0.47
    MAX_ASPECT_RATIO = 0.67
    url = fix_image_url(post.url)
    W, H = get_image_size(url)
    if W is None:
        print("bad: could not read dimensions. url: %s\n" %url,end='')
        return False

    if not(MIN_ASPECT_RATIO < H/W < MAX_ASPECT_RATIO):
       print("bad: aspect ratio incompatible (%dx%d) %s.\turl: %s\n"  \
            %(W,H,str(round(H/W,2)),url),end='')
       return False
    
    if H*W < MIN_RESOLUTION:
       print("bad: resolution too low (%dx%d).\turl: %s\n"  %(W,H,url),end='')
       return False
       
    print("good. (%dx%d).\turl: %s\n"  %(W,H,url),end='')
    return True

def filter_text(post):
    """
    Decide if the text fits this scripts requirements:
       * All text posts must be shorter than 140 charecters.
    
    Args:
        post: a single praw post object
    
    Returns:
        Boolean of validity
    """
    if len(post.title) > 140: #tweet length, for tl;dr reasons.
        print('bad: too long.')
        return False
    print('good.')
    return True 

def get_valid_posts(reddit,subName,outputSize,filterFunc,index):
    """
    Get the top N posts that qualify by filter (or as close as possible to it)

    Args:
        subName (string): Name of the subreddit.
        outputSize (int): The size of the array to return 
            (not promised, best effort only)
        filterFunc (function): function that recieves a post object and returns
            a boolean of its validity.
        maxTries (int): only check this ammount of posts before stopping.
    
    Returns:
        An array of valid posts.
    """
    maxTries = 100 #Maximum Reddit API allows.
    result =[]
    postArr = reddit.get_subreddit(subName).get_hot(limit=maxTries)
    i = 1
    try:
        for post in postArr:
            print(subName+": Try",(i)," got", index+len(result) ," checking ... ",end='')
            post = next(postArr)
            if filterFunc(post):
                result.append(post)
            if len(result)==outputSize:
                print("got",index+len(result),". done.")
                return result
            i+=1
    except StopIteration:
        pass
    print("tries limit reached. continuing with",len(result))
    return result

def get_posts(reddit,subreddits,limit,filterFunc):
    """
    Get up to <limit> posts that are approved by <filterFunc>
    from all <subreddits>, by order.
    All valid posts are taken from subreddit i, before moving to i+1
    
    Args:
        reddit (praw.Reddit): reddit object
        subreddits (array of strings): All the subreddits names (no r/), 
            by priority. ["FisrtPrioritySub","SecondPrioritySub",...]
        limit (int): Get up to this ammount of posts.
        filterFunc (function): recieves a post object and returns a 
            boolean of its validity. 
    
    Returns:
        A list of post objects
    """
    result =[]
    for subreddit in subreddits:
        if len(result) >= limit:
            break
        print(subreddit,":")
        found = len(result)
        required = limit-found
        result.extend(get_valid_posts(reddit,subreddit,required, filterFunc,found))
        print("total of %d posts acquired."%len(result))
    return result
    
def get_reddit_content(image_subreddits,text_subreddits,limit):
    """
    Get an array of reddit posts to be used 
    
    Args:
        subName (string): Name of the subreddit.
        outputSize (int): The size of the array to return
            (not promised, best effort only)
        filterFunc (function): recieves a post object and returns  
            a boolean of its validity.
        maxTries (int): only check this ammount of posts before stopping.
    
    Returns:
        A tuple of arrays: ([array of image urls], [array of text strings])
    """
    print("connectig to reddit.com")
    reddit = praw.Reddit(user_agent="ChromecastBackdrop")
    print("getting image posts")
    imagePosts = get_posts(reddit,image_subreddits,limit,filter_image)

    if len(imagePosts)==0:
        print("No images found.")
        return [],[]
    
    print("getting text posts")
    textLimit = len(imagePosts)
    textPosts= get_posts(reddit,text_subreddits,textLimit,filter_text)
    images = [fix_image_url(post.url) for post in imagePosts]
    texts = [post.title for post in textPosts]
    
    return images,texts

def download_image(url, path):
    """
    Download an image by URL.
    
    Args:
        path (string): destination file path. 
        name (string): name of the destination file.
    """
    #Label image using current date and image in sequence.
    resource = urllib2.urlopen(url)
    output = open(path,"wb")
    output.write(resource.read())
    output.close()

def multiline_text(text, image_width, image_height, font):
    """
    Splits large text up into multiple lines by using newlines so
    that it fits onto the given image dimensions.
    The text is to fit within 2/3 of the image width. 
    
    Args:
        text (string): the single line text to fit into multiple lines
        image_width (int): the width of the image to fit the text onto
        image_height (int): the height of the image to fit the text onto

    Returns:
        string: the given text with added newlines
    """
    tail = text
    length = 0
    while font.getsize(tail)[0] > 2*image_width/3:
        head = tail
        while font.getsize(head)[0] > 2*image_width/3:
            head = head.rsplit(' ', 1)[0]
        length += len(head)
        tail = tail[length:]
        text = text[:length] + '\n' + text[length:]
        length += len("\n")
    return text

def draw_border(draw,w,h,text,font,color,borderRadius,borderResolusion):
    """
    Draws a a background on which text can be placed,
    to create a contrasted border. It does so by drawing the text, in copies,
    on the radius of a circle with a given radius. 
    The resolution determines how many instances of text will be written
    (The angles will be the entire circle divided equaly)
    
    Args:
        draw (ImageDraw.Draw): draw object to place the text over. 
        text (string): the text to draw over the image.
        w (int): this is the x position of where to put the top left corner of
            the text. Different for single line and multiline text.
        h (int): this is the y position of where to put the top left
            corner of the text.
        font (
        color: color code, either in string form like "white" 
            or tuple like (255,255,255) (transparency not supported).
     
    """    
    bordersX = []
    tau = 2*math.pi
    for i in range(borderResolusion):
        bordersX.append(borderRadius*round(math.cos(i*tau/borderResolusion),2))
    bordersY = []
    for i in range(borderResolusion):
        bordersY.append(borderRadius*round(math.sin(i*tau/borderResolusion),2))
    
    for x,y in zip(bordersX,bordersY):
        draw.multiline_text((w + x, h + y), text, font=font,
                            align='center', spacing=5, fill=color)

def draw_text(image, text,font, borderRadius = 6, borderResolusion = 20):
    """
    Draws the text over the given image object.

    Args:
        image (ImageDraw): the actual image to draw the text over. note that
            this is not the file but the actual ImageDraw object created
            from the image file.
        text (string): the text to draw over the image.
        w (int): this is the x position of where to put the top left corner of
            the text. Different for single line and multiline text.
        h (int): this is the y position of where to put the top left 
            corner of the text.
        borderRadius (int) optional, radius of border for the text.
        borderResolusion (int) optional, how many times the 
    """
    draw = ImageDraw.Draw(image)
    h = (image.size[1] - ((text.count('\n')+1) *\
                          (font.getsize(text)[1] + 5)))/2
    if text.count('\n') > 0:
        w = image.size[0]/6
    else:
        w =(image.size[0]-font.getsize(text)[0])/2
    
    draw_border(draw,w,h,text,font,'black',borderRadius,borderResolusion)
    
    draw.multiline_text((w, h), text, font=font,
                        align='center', spacing=5, fill="white")

def generate_image(backgroundImagePath,text, fontPath, destFilePath = None):
    """
    Creates an image file with text written over a background image.
    Overwrites the image in backgroundImagePath.
    
    Args:
        backgroundImagePath (string): Path to the image file. 
            Assumes file exists.
        text (string): The text to draw over the image.
        fontPath (string): path to the font file to be used.
        destFilePath (string) optional, where to save the result
            default is to overwrite the file in backgroundImagePath.
    """
    if destFilePath == None:
        destFilePath = backgroundImagePath
    img = Image.open(backgroundImagePath)
    width, height = img.size
    font = ImageFont.truetype(fontPath, int(height*.04))
    textMultiLine = multiline_text(text, width, height,font)
    draw_text(img, textMultiLine,font)
    img.save(destFilePath, "JPEG", quality=100, \
        optimize=True, progressive=True)

def create_images(images,texts,destDir,fontPath):
    """
    create image files with text from texts and background from images 
    in destDir.
    
    Args:
        images (array of strings): urls of images. Assumes the images exist.
        texts (array of strings): texts to insert to images.
        destDir (string): local path where the files will be saved.        
        fontPath (string): path to the font file to be used.        
    
    Returns:
        An array of valid posts.
    """    
    i = 1
    for image,text in zip(images,texts):
        print("%d: downloading %s ..." %(i,image),end='')
            
        imageName = time.strftime("%Y-%m-%d.%H-%M-%S")+"-"+str(i)+'.jpg'
        localImagePath = os.path.join(destDir,imageName)
        download_image(image,localImagePath)
        print("creating image %s" %localImagePath)
        generate_image(localImagePath,text,fontPath)
        i+=1
    print("done.")
    print("all finished.")

def run(limit,imageSubreddits,textSubreddits,destDir,fontPath):
    """
    create image files with text from textSubreddits ,
    and background from imageSubreddits.
    
    Args:
        limit (int): The maximum number of images to create.
        imageSubreddits (list of strings): all subreddits to take images from,
            orderd by priority, no "r/" 
        textSubreddits (list of strings): all subreddits to take text from,
            orderd by priority, no "r/" 
        destDir (string): local path where the files will be saved.
        fontPath (string): path to the font file to be used.                
    """    
    
    images, texts = get_reddit_content(imageSubreddits,textSubreddits,limit)
    create_images(images,texts,destDir,fontPath)
    
class ShinyChromeShowerConfig():
    def __init__(self,limit=0,imageSubreddits=[],textSubreddits=[],destDir='',fontPath=''):
        """
        Create configuration object.
        
        Args:
            limit (int): The maximum number of images to create.
            imageSubreddits (list of strings): all subreddits to take images from,
                orderd by priority, no "r/" 
            textSubreddits (list of strings): all subreddits to take text from,
                orderd by priority, no "r/" 
            destDir (string): local path where the files will be saved.
            fontPath (string): path to the font file to be used.
        """  
        self.limit           = limit
        self.imageSubreddits = imageSubreddits
        self.textSubreddits  = textSubreddits 
        self.destDir         = destDir
        self.fontPath        = fontPath
        
    def load_file(self,filePath):
        """
        Load configuration object with data from config file.
        Fails if a parameter is missing.
        
        Args:
            filePath (string): Path to configuration file.
        """
        config = ConfigParser.ConfigParser()
        config.read(filePath)
        self.limit           = config.getint('Settings','limit'           )
        self.destDir         = config.get('Settings',   'dest_dir'        )
        self.fontPath        = config.get('Settings',   'font_path'       )
        self.imageSubreddits = config.get('Settings',   'image_subreddits').split()
        self.textSubreddits  = config.get('Settings',   'text_subreddits').split()

    def load_namespace(self,namespace):
        """
        Adds parameters from a namespace object.
        Keeps existing value if a parameter is missing.
        
        Args:
            namespace (Namespace object): Every parameter loaded to the object will
                be copied to the configuration file.
        """
        try:
            self.limit           = namespace.limit
        except AttributeError: pass
        try:
            self.imageSubreddits = namespace.imageSubreddits
        except AttributeError: pass

        try:
            self.textSubreddits  = namespace.textSubreddits
        except AttributeError: pass

        try:
            self.destDir         = namespace.destDir
        except AttributeError: pass

        try:
            self.fontPath        = namespace.fontPath
        except AttributeError: pass
        
    def _list2str(self,l):
        """
        Converts a list object to a string separated by spaces.

        Args:
            l (list of strings): strings to join

        Returns:
            A joined string.
        """       
        s=''
        for i in l:
            s+=str(i)+" "
        return s[:-1]

    def write(self,filePath):
        """
        Saves the current configuration to file.

        Args:
            filePath (string): Path to configuration file.
        """           
        cfgfile = open(filePath,'w')
        config = ConfigParser.ConfigParser()       
        
        config.add_section('Settings')
        config.set('Settings','limit'            ,str(self.limit))
        config.set('Settings','image_subreddits' ,self._list2str(self.imageSubreddits))
        config.set('Settings','text_subreddits ' ,self._list2str(self.textSubreddits))
        config.set('Settings','dest_dir'         ,self.destDir)
        config.set('Settings','font_path'        ,self.fontPath)    

        config.write(cfgfile)
        cfgfile.close()

if __name__ == "__main__":
    #Default config
    config = ShinyChromeShowerConfig(
        limit           = 10,
        imageSubreddits = ["EarthPorn","SpacePorn","WaterPorn","SkyPorn","WinterPorn","FirePorn","WeatherPorn","SeaPorn"],
        textSubreddits  = ["Showerthoughts"],
        destDir         = get_resource_path('results'),
        fontPath        = get_resource_path("Roboto-Light.ttf"),
    )
    defaultConfigPath   = get_resource_path('config.ini')
    
    #Load configuration
    if os.path.isfile(defaultConfigPath):
        config.load_file(defaultConfigPath)    
    else:
        print("No config.ini file found. creatig default config file.")
        config.write(defaultConfigPath)
    
    #Command line arguments
    argparser = argparse.ArgumentParser(description='ShinyChromeShower')

    def check_positive(value): #Checks value of limit.
        ivalue = int(value)
        if ivalue < 0:
            raise argparse.ArgumentTypeError("%s is an invalid positive int value" % value)
        return ivalue
    
    def check_font_path(value): #Checks value of fontPath.
        if not os.path.isfile(value):
            raise argparse.ArgumentTypeError("%s is not a file." % value)
        return value
    
    #add_argument 
    argparser.add_argument("--config-file","-c", default=defaultConfigPath,type=str,
        help="The path of the configuration file. This option overrides all others.", 
        metavar="config_file_path", dest="configPath")      
    argparser.add_argument("--limit","-l",default=config.limit, type=check_positive,
        help="The maximum number of images to create.", 
        metavar="number", dest="limit")
    argparser.add_argument("--image-subs","-i", nargs="+",default=config.imageSubreddits,
        help='''All the subreddits to take images from.
        first all the available fitting photos
        will be taken from the first, and then the next and so on. 
        Subreddit names should not contain r/''', 
        metavar="subreddit_name", dest="imageSubreddits")
    argparser.add_argument("--text-subs","-t", nargs="+",default=config.textSubreddits,
        help='''All the subreddits to take text lines from. 
        first all the available fitting text titles (under 140 charecters)
        will be taken from the first, and then the next and so on. 
        Subreddit names should not contain r/''', 
        metavar="subreddit_name", dest="textSubreddits")
    argparser.add_argument("--dest","-d", type=str,default=config.destDir,
        help="The directory where the images will be created", 
        metavar="directory_path", dest="destDir")    
    argparser.add_argument("--font","-f",type=check_font_path,default=config.fontPath,
        help="The path of the .ttf font file.", 
        metavar="font_path", dest="fontPath")      
    
    argparams = argparser.parse_args()
    
    #Process parameters
    try:
        config.load_file(argparams.configPath)
    except:
        config.load_namespace(argparams)
    
    if not os.path.exists(config.destDir):
        os.makedirs(config.destDir)

    #Run.
    run(config.limit,\
        config.imageSubreddits,\
        config.textSubreddits,\
        config.destDir,\
        config.fontPath)
         
