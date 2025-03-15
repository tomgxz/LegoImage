from PIL import Image, ImageDraw
from pathlib import Path

import os

from utils import colors
from utils.paths import ASSETS_DIR, OUTPUT_DIR


class Stud():
    """ Represents a LEGO-like stud with customizable color, radius, and optional text image.

    This class allows the creation of a stud object with a specified color and radius. The stud is represented
    as a circular shape with color and shading effects, and optionally a text image that can be added to the stud.
    The stud's color is stored as a `colors.Color` object, and its image is generated and drawn based on the specified attributes.
    """
    
    def __init__(self, color:colors.Color, radius:int, text_image:Image = None):
        """ Initializes a Stud object with a given color, radius, and optional text image.

        :param color: The color of the stud, as a `colors.Color` object.
        :type color: colors.Color
        :param radius: The radius of the stud, in pixels, which determines its size.
        :type radius: int
        :param text_image: Optional image to be placed on the stud, defaults to None
        :type text_image: PIL.Image, optional
        """
        
        self.color:colors.Color = color.copy()
        self.radius:int = radius
        self.text_image = text_image
        
        self.empty = self.color.alpha == 0
        self.uses:int = 0

        self.image:Image = Image.new("RGBA", (self.diameter, self.diameter), color = colors.TRANSPARENT.rgb255)
        self.draw = ImageDraw.Draw(self.image)
    
    def __del__(self):
        """ Cleans up the resources used by the Stud object. \n
        This method ensures that memory is freed when the Stud object is deleted.
        """
        del self.image
        del self.draw
    
    @property
    def diameter(self) -> int:
        """ Calculates and returns the diameter of the stud in pixels.
        
        :return: The diameter of the stud.
        :rtype: int
        """
        return self.radius * 2

    def add_use(self):
        """ Increments the usage count for the stud. """
        self.uses += 1
        
    def make_stud_image(self):
        """ Generates the stud image, drawing the stud with its color, and adding a text image (if available).

        The stud is drawn as a circular shape with three layers:
        - The main color of the stud.
        - A black inset circle.
        - A darker inset circle for shading.
        
        If a text image is not provided, a default text image is used.

        :return: True if the stud image was successfully generated, False if the stud is empty (transparent).
        :rtype: bool
        """
        
        if self.empty:
            return False
        
        self.draw.ellipse([0, 0, self.diameter, self.diameter], fill = self.color.rgb255)
        
        inset = self.diameter / 6
        difference = self.diameter / 15
        
        self.draw.ellipse([inset+difference, inset+difference, self.diameter-inset+difference, self.diameter-inset+difference], fill = colors.BLACK.rgb255)
        
        inset = self.diameter / 5
        darker = self.color.copy().darken(0.3)
        
        self.draw.ellipse([inset, inset, self.diameter-inset, self.diameter-inset], fill = darker.rgb255)
        
        if self.text_image is None:
            self.text_image = self.image_parent.open("assets/img/legotext.png").rotate(15, expand=True)
            new_x = inset * 2
            self.text_image = self.text_image.resize(int(new_x), int((1 / (self.text_image.size[0] / new_x)) * self.text_image.size[1]), Image.Resampling.LANCZOS)
    
        self.image.paste(self.text_image, (int(self.radius - (self.text_image.size[0] / 2)), int(self.radius - (self.text_image.size[1] / 2))), self.text_image)

        return True


class PixelMap(object):
    def __init__(self, 
                 path, 
                 greyscale = False, 
                 newx = 64,
                 transparent_color = colors.TRANSPARENT, 
                 transparent_margin = 0.5, 
                 background_color = colors.TRANSPARENT, 
                 keep_removed_transparent_studs = False, 
                 transparent_background = True, 
                 stud_resolution = 96, 
                 color_replace = {}, 
                 limit_to_lego_only = False, 
                 reduce_color = -1
        ):
        
        self.image_draw = ImageDraw
        
        class Options:
            def __init__(self):
                self.filter_greyscale:bool = greyscale
                self.keep_removed_transparent_studs:bool = keep_removed_transparent_studs
                
                self.transparent_color:colors.Color = colors.Color(transparent_color)
                self.transparent_margin = transparent_margin
                
                self.background_color:colors.Color = colors.Color(background_color) if not transparent_background else colors.TRANSPARENT
                self.stud_resolution:int = stud_resolution
                self.limit_to_lego_only:bool = limit_to_lego_only
                
                self.replace_colors:bool = len(color_replace) and not limit_to_lego_only
                self.replace_colors_dict:dict = color_replace if not limit_to_lego_only else {}
                
                self.reduce_color:bool = reduce_color > 0
                self.reduce_color_layers:int = reduce_color
            
        self.options = Options()
        
        self.path = path
        self.imageName = os.path.basename(path).split(".")[0]
        self.loadImage()

        self.studs = list()
        self.pixel_map: list[list[colors.Color]] = list() # A 2 dimensional list of the colors of each pixel
        self.image_colors: list[colors.Color] = list()
        
        self.color_filter = dict() # A map between the image color and its closest lego color
        self.color_filter_uses: dict[str, int] = dict() # Counts the amount of times a filtered color is used

        self.resize(newx)

        print("Image Loaded")

        self.toMap()

        print("Map Generated")

        if self.options.limit_to_lego_only:
            self.generateFilter()
            print("Generated Filter Dictionary")

        self.generateImage()

        print("Image Saved")


    def drawStud(self, image, coords, radius, fill:colors.Color, stud_text_image = None):        
        # Deep copy the color to preserve it in the pixel_map list whilst performing edits here
        fill = fill.copy()
        
        fill.alpha = 1 if fill.alpha >= self.options.transparent_margin else 0

        if not fill.alpha and self.options.keep_removed_transparent_studs:
            fill = self.options.transparent_color.copy()
        
        stud = Stud(fill, radius, stud_text_image)
        
        if stud in self.studs:
            # Replace with the existing instance
            stud = next(existing_stud for existing_stud in self.studs if existing_stud == stud)
            
        stud.make_stud_image()

        if not stud.empty:
            if self.options.replace_colors and str(fill) in self.options.replace_colors_dict:
                fill = self.options.replace_colors_dict[str(fill)]

            if self.options.limit_to_lego_only and str(fill) in self.color_filter:
                fill = self.color_filter[str(fill)]

                # get index of fill, increase by 1
                self.color_filter_uses[str(fill)] += 1
        
        image.paste(stud.image, (coords[0], coords[1]))


    def toMap(self):
        for x in range(self.image_width):
            for y in range(self.image_height):
                pixel_color = colors.Color(
                    colors.ColorConv.base_255_to_1(self.pixels[x,y])
                )
                
                if pixel_color not in self.image_colors:
                    self.image_colors.append(pixel_color)
                    
                if len(self.pixel_map) < y + 1: 
                    self.pixel_map.append(list())
                
                self.pixel_map[y].append(pixel_color)


    def generateImage(self):

        def preloadStudText(radius):
            text = Image.open(ASSETS_DIR / "img" / "legotext.png").rotate(15, expand=True)
            
            diameter = radius * 2
            inset = diameter / 5
            new_x = inset * 2
            
            text = text.resize((int(new_x), int((1 / (text.size[0] / new_x)) * text.size[1])), Image.Resampling.LANCZOS)
            return text

        stud_radius = self.options.stud_resolution
        stud_diameter = stud_radius * 2
        preloaded_stud_text = preloadStudText(stud_radius)

        new_image = Image.new("RGBA", (stud_diameter * self.image_width, stud_diameter * self.image_height), color = colors.BLACK.rgb255)
        
        for y in enumerate(self.pixel_map):
            for x in enumerate(y[1]):                
                coords = [x[0] * stud_diameter, y[0] * stud_diameter, (x[0]+1) * stud_diameter, (y[0]+1) * stud_diameter]
                
                fill_color = self.pixel_map[y[0]][x[0]]
                if self.options.limit_to_lego_only:
                    fill_color = self.color_filter[str(fill_color)]
                
                self.drawStud(new_image, coords, stud_radius, fill_color, stud_text_image = preloaded_stud_text)
        
        print("Image Generated")

        new_image.save(OUTPUT_DIR / self.imageName / f"{self.imageName}_lego{"_limit" if self.options.limit_to_lego_only else ""}.png")


    def loadImage(self):
        self.image = Image.open(self.path)

        self.reduceColor()

        self.pixels = self.image.load()
        self.image_width, self.image_height = self.image.size


    def resize(self, new_x):
        if new_x == None: 
            resize_to = (self.image_width, self.image_height)
        else:
            if new_x > self.image_width:
                raise Exception(
                    "New size cannot be larger than the original image")

            proportion = 1 / (self.image_width / new_x)
            resize_to = (int(new_x), int(proportion * self.image_height))

        self.image = self.image.resize(resize_to, Image.Resampling.LANCZOS)

        self.reduceColor()

        self.pixels = self.image.load()
        self.image_width, self.image_height = self.image.size


    def generateFilter(self):
        new_color_map:list[colors.Color] = list()
        
        # Set all colors alpha to 1
        for original_color in self.image_colors:
            new_color = original_color.copy()
            new_color.alpha = 1
            
            new_color_map.append(new_color)

            differences:list[float] = []
            
            # Get the difference value for every color in the lego set
            for compare in colors.LEGO_COLORS_LIST:
                differences.append(new_color.diff(compare))
            
            closest_color_index = differences.index(min(differences))
            closest_color = colors.LEGO_COLORS_LIST[closest_color_index]
            
            # set the color in the filter map to the color with the smallest difference value
            self.color_filter[str(original_color)] = closest_color
            
            # Add the new color to the filter index list
            if str(closest_color) not in self.color_filter_uses.keys():
                self.color_filter_uses[str(closest_color)] = 0 # Counter for how many times this color is used


    def reduceColor(self):
        """ Reduces the amount of unique colors in the image based on the user input """
        if self.options.reduce_color:
            self.image = self.image.convert("P", palette=Image.Palette.ADAPTIVE, colors=self.options.reduce_color_layers)
            self.image = self.image.convert("RGB")
            self.image.show()


USE_DEBUG_OPTIONS = True

if USE_DEBUG_OPTIONS:
    name = "rags"
    path = OUTPUT_DIR / name / f"{name}.png"
else:
    path = input("Please enter the path of the image you want to turn into lego\n\n\tImage should be in png format\n\tRemember to add the filetype on the end of the path (eg .png)\n\tIf the image is in the same directory, you only need to put the name and the filetype (eg \"img.png\")\n\tIf it is in any other directory, you will need the full path (eg \"C:\\Users\\Lego\\Pictures\\img.png\")\n\n")

from os import access, R_OK
from os.path import isfile

while True:
    try:
        path = Path(path).resolve(strict=True)
        assert isfile(path) and access(path, R_OK), f"File {path} doesn't exist or isn't readable"
    except Exception as e:
        print(f"Error with given path: {e}\n")
        path = input("Please try again\n\n")
    else:
        break
    
if USE_DEBUG_OPTIONS:
    WIDTH_STUDS = 96
    LIMIT_TO_LEGO_ONLY = True
else:
    WIDTH_STUDS = int(input("\nHow many studs wide would you like the image to be?\n\n\tPlease bear in mind that the larger this value, the larger the file size.\n\tIf you wish to keep the amount of studs but reduce file size, the variable\n\tstudRadius, in the function generateImage, in the class PixelMap can be decreased\n\tThis is not recommended, a wiser path would be to then resize it in an image editor.\n\tIf you do edit it, the default value is 96. The recommended stud width is 64.\n\tCombining these two values will give you a png image of width 12'288 pixels.\n\tA square image will therefore result in a png image of size ~4.83MB.\n\n"))
    LIMIT_TO_LEGO_ONLY = input("\nDo you want the image to be filtered to Lego default colors. (yes/no)\n\n").lower()=="yes"
    print()

pixel_map = PixelMap(path, newx=WIDTH_STUDS, stud_resolution=72, limit_to_lego_only=LIMIT_TO_LEGO_ONLY, reduce_color=-1)

if LIMIT_TO_LEGO_ONLY:
    sorted_byuses = dict(sorted(pixel_map.color_filter_uses.items(), key=lambda item: item[1], reverse=True))
    print(pixel_map.color_filter_uses)

    with open(str(path) + ".cl", "w") as f:
        f.write("Colors used in image\n\n")
        
        for key, value in sorted_byuses.items():
            color_id = "COLOR ID"
            color_hexcode = "HEX CODE"
            color_uses = value
            color_name = "COLOR NAME"
            f.write(f"{color_id}\t\t{color_hexcode}\t\t{color_uses}\t\t{color_name}\n")
