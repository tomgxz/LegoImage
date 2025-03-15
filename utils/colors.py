from enum import Enum
from numbers import Number
from typing import Iterable, Tuple
import copy, math

class ColorConv():
    """
    A utility class for converting between color representations and normalizing color values between different scales.

    This class provides functions to:
    - Convert between RGB and HSL color spaces (normalized between 0 and 1).
    - Convert color values between the 0-255 integer range and the normalized 0-1 range.
    - Clamp normalized color values to ensure precise 8-bit representation.
    """
    
    @staticmethod
    def rgb_to_hsl(r:float, g:float, b:float) -> tuple[float, float, float]:
        """ Converts an RGB color to HSL (Hue, Saturation, Lightness), where the input and output colors are normalized between 0 and 1.
        - Uses normalized RGB values (0 to 1) instead of 0-255.
        - The Hue wraps around if negative to stay within [0,1].
        - An achromatic color (where r = g = b) results in a saturation of 0.

        :param r: Red component, normalized (0 ≤ r ≤ 1)
        :type r: float
        :param g: Green component, normalized (0 ≤ g ≤ 1)
        :type g: float
        :param b: Blue component, normalized (0 ≤ b ≤ 1)
        :type b: float
        
        :return: The HSL representation, each component normalized between 0 and 1.
            index 0 (float): Hue, normalized (0 ≤ h ≤ 1), where 0 and 1 represent red.
            index 1 (float): Saturation (0 ≤ s ≤ 1), where 0 is grayscale and 1 is fully saturated.
            index 2 (float): Lightness (0 ≤ l ≤ 1), where 0 is black and 1 is white.
        :rtype: tuple[float, float, float]
        """
        
        # Find the minimum and maximum values of the RGB components
        cmax = max(r, g, b)
        cmin = min(r, g, b)
        delta = cmax - cmin
        
        # Initialize H, S, L
        h = 0
        s = 0
        l = (cmax + cmin) / 2
        
        # If there is no difference (cmax == cmin), the color is achromatic (gray)
        if delta != 0:
            # Calculate Saturation
            if l < 0.5:
                s = delta / (cmax + cmin)
            else:
                s = delta / (2.0 - cmax - cmin)
            
            # Calculate Hue
            if cmax == r:
                h = (g - b) / delta
            elif cmax == g:
                h = (b - r) / delta + 2
            elif cmax == b:
                h = (r - g) / delta + 4
            
            # Ensure the Hue is between 0 and 1
            h /= 6
            
            # If hue is negative, wrap it around by adding 1
            if h < 0:
                h += 1
    
        return (h, s, l)

    @staticmethod
    def hsl_to_rgb(h:float, s:float, l:float) -> tuple[float, float, float]:
        """ Converts an HSL color to RGB, where the input and output colors are normalized between 0 and 1

        :param h: Hue, normalized (0 ≤ h ≤ 1), where 0 and 1 represent red.
        :type h: float
        :param s: Saturation (0 ≤ s ≤ 1), where 0 is grayscale and 1 is fully saturated.
        :type s: float
        :param l: Lightness (0 ≤ l ≤ 1), where 0 is black and 1 is white.
        :type l: float
        
        :return: The HSL representation, each component normalized between 0 and 1.
            index 0 (float): Red component, normalized (0 ≤ r ≤ 1)
            index 1 (float): Green component, normalized (0 ≤ g ≤ 1)
            index 2 (float): Blue component, normalized (0 ≤ b ≤ 1)
        :rtype: tuple[float, float, float]
        """
        
        # Chroma calculation
        c = (1 - abs(2 * l - 1)) * s
        
        # X calculation (for intermediate RGB values)
        x = c * (1 - abs(((h * 6) % 2) - 1))
        
        # m calculation (adds the offset to the RGB values)
        m = l - c / 2
        
        # RGB values (before adjustment with m)
        if 0 <= h < 1 / 6:
            r_prime, g_prime, b_prime = c, x, 0
        elif 1 / 6 <= h < 2 / 6:
            r_prime, g_prime, b_prime = x, c, 0
        elif 2 / 6 <= h < 3 / 6:
            r_prime, g_prime, b_prime = 0, c, x
        elif 3 / 6 <= h < 4 / 6:
            r_prime, g_prime, b_prime = 0, x, c
        elif 4 / 6 <= h < 5 / 6:
            r_prime, g_prime, b_prime = x, 0, c
        else:
            r_prime, g_prime, b_prime = c, 0, x
        
        # Adjust RGB values with m
        r = (r_prime + m)
        g = (g_prime + m)
        b = (b_prime + m)
        
        # Return RGB values between 0 and 1
        return (r, g, b)

    @staticmethod
    def rgb_to_hex(r: float, g: float, b: float, a: float = None) -> str:
        """ Converts an RGB color to a hex code, where the input components are normalized between 0 and 1.
        - Uses normalized RGB values (0 to 1) instead of 0-255.
        - If alpha is present, creates an 8 character long hex code, plus hashtag
        - If not, creates a 6 character long hex code, plus hashtag

        :param r: Red component, normalized (0 ≤ r ≤ 1)
        :type r: float
        :param g: Green component, normalized (0 ≤ g ≤ 1)
        :type g: float
        :param b: Blue component, normalized (0 ≤ b ≤ 1)
        :type b: float
        :param b: Optional alpha component, normalized (0 ≤ b ≤ 1), defaults to None
        :type b: float, optional
        
        :return: The hexadecimal representation, either 6 or 8 characters long, including a hashtag
        :rtype: str
        """
        r, g, b = ColorConv.base_1_to_255((r, g, b))
        
        if a is not None:
            a = a * 255
            return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
        
        return f"#{r:02x}{g:02x}{b:02x}"

    @staticmethod
    def hex_to_rgb(hex_value: str) -> tuple[float, float, float, float]:
        """ Converts a HEX color to RGB
        - In the case of alpha not being present, it is assumed to be opaque

        :param hex_value: The hexadecimal representation of the color, optionally can include alpha, optionally can include a prefix hashtag
        :type hex_value: str
        
        :return: The RGB representation, including alpha, each component normalized between 0 and 1.
        :rtype: tuple[float, float, float]
        """
        
        # Remove the '#' if it's there
        hex_value = hex_value.lstrip('#')
        if len(hex_value) not in [6, 8]:
            raise ValueError("HEX color should be in the format #RRGGBB, RRGGBB, #RRGGBBAA or RRGGBBAA")

        # Extract RGB components as 8-bit values
        r = int(hex_value[0:2], 16)
        g = int(hex_value[2:4], 16)
        b = int(hex_value[4:6], 16)
        
        if len(hex_value) == 8:
            a = int(hex_value[6:8], 16)
        else:
            a = 1
        
        return ColorConv.base_255_to_1((r, g, b, a))


    @staticmethod
    def base_255_to_1(color_iterable: Iterable[int]) -> Tuple[float, ...]:
        """ Converts color values from the 8-bit 0-255 range to the normalized 0-1 range.

        :param color_iterable: An iterable of 8-bit integer color values (0 ≤ x ≤ 255)
        :type color_iterable: Iterable[int]
        :return: A tuple of normalized color values (0 ≤ x ≤ 1)
        :rtype: Tuple[float, ...]
        """
        
        return tuple(map(lambda x: x / 255, color_iterable))

    @staticmethod
    def base_1_to_255(color_iterable: Iterable[float]) -> Tuple[int, ...]:
        """ Converts color values from the normalized 0-1 range to the 8-bit 0-255 range.

        :param color_iterable: An iterable of float color values (0 ≤ x ≤ 1)
        :type color_iterable: Iterable[float]
        :return: A tuple of 8-bit integer color values (0 ≤ x ≤ 255)
        :rtype: Tuple[int, ...]
        """
        
        return tuple(map(lambda x: round(x * 255), color_iterable))

    @staticmethod
    def clamp_to_255_res(color_iterable: Iterable[float]) -> Tuple[float, ...]:
        """ Clamps normalized color values (0-1) to the closest representable value in the 8-bit 0-255 integer space.
        Ensures that converting back to 0-255 results in an exact integer representation.

        :param color_iterable: An iterable of float color values (0 ≤ x ≤ 1).
        :type color_iterable: Iterable[float]
        :return: A tuple of normalized color values (0 ≤ x ≤ 1), rounded to the nearest 1/255 step.
        :rtype: Tuple[float, ...]
        """
        
        return tuple(map(lambda x: round(x * 255) / 255, color_iterable))


class ColorMode(Enum):
    RGB = 0
    HSL = 1
    RGB255 = 2
    HSL255 = 3
    HEX = 4


class Color():
    """ A class for handling colors with both RGB and HSL representations, supporting conversions, clamping, and basic color manipulations.

    Supports:
    - RGB and HSL color models, with values normalized between 0 and 1.
    - 8-bit (0-255) color representation for RGB and HSL.
    - Alpha (opacity) values, defaulting to 1 (fully opaque).
    - Lightening and darkening functions.
    - Color difference measurement in HSL space.
    """
    
    def __init__(self, initial:Iterable[Number]|str = None, _as:ColorMode = ColorMode.RGB):
        """
        :param initial: Initial color value, as an iterable of float color values, defaults to None
        :type initial: Iterable[Number] | str, optional
        :param _as: Color Mode describing the initial color value, defaults to ColorMode.RGB
        :type _as: ColorMode, optional
        """
        
        # Defaults to opaque black
        self.__r: float = 0.0
        self.__g: float = 0.0
        self.__b: float = 0.0
        self.__a: float = 1.0 
        
        if initial is not None:
            if isinstance(initial, __class__):
                self = initial
            
            elif isinstance(initial, str) and _as == ColorMode.HEX:
                # If the input is a HEX color
                self.hex = initial
                
            elif isinstance(initial, (list, tuple)) and 2 < len(initial) < 5:
                if _as == ColorMode.RGB:
                    self.rgb = initial
                elif _as == ColorMode.HSL:
                    self.hsl = initial
                elif _as == ColorMode.RGB255:
                    self.rgb = ColorConv.base_255_to_1(initial)
                elif _as == ColorMode.HSL255:
                    self.hsl = ColorConv.base_255_to_1(initial)

    @property
    def rgb(self) -> tuple[float, float, float, float]:
        """ Returns the color in normalized RGB format (0 to 1).

        :return: A tuple representing the RGB values (r, g, b, alpha) where each component is between 0 and 1.
        :rtype: tuple[float, float, float, float]
        """
        return self.__r, self.__g, self.__b, self.__a
    
    @property
    def rgb255(self) -> tuple[float, float, float, float]:
        """ Returns the color in 8-bit (0-255) RGB format.

        :return: A tuple representing the RGB values (r, g, b, alpha) where each component is between 0 and 255.
        :rtype: tuple[int, int, int, int]
        """
        return ColorConv.base_1_to_255((self.__r, self.__g, self.__b, self.__a))
    
    @rgb.setter
    def rgb(self, value: Tuple[float, ...]):
        """ Sets the color using normalized RGB values (0 to 1). Optionally includes an alpha component.
        
        :param value: A tuple of RGB values (r, g, b) with optional alpha (a), where 0 ≤ r, g, b ≤ 1 and 0 ≤ a ≤ 1.
        :type value: Tuple[float, ...]
        
        :raises AssertionError: If any of the RGB values or the alpha value (if provided) are out of bounds.
        """
        assert 0 <= value[0] <= 1 and 0 <= value[1] <= 1 and 0 <= value[2] <= 1, \
            "RGB values must be between 0 and 1"
        
        if len(value) > 3:
            assert 0 <= value[3] <= 1, "Alpha value must be between 0 and 1"
            self.__a = value[3]
        
        self.__r, self.__g, self.__b, self.__a = ColorConv.clamp_to_255_res(list(value[:3]) + [self.__a])


    @property
    def hsl(self) -> tuple[float, float, float, float]:
        """ Returns the color in normalized HSL format (0 to 1).

        :return: A tuple representing the HSL values (h, s, l, alpha) where each component is between 0 and 1.
        :rtype: tuple[float, float, float, float]
        """
        h, s, l = ColorConv.rgb_to_hsl(*self.rgb[:3])
        return h, s, l, self.__a
    
    @property
    def hsl255(self) -> tuple[float, float, float, float]:
        """ Returns the color in 8-bit (0-255) HSL format.

        :return: A tuple representing the HSL values (h, s, l, alpha) where each component is between 0 and 255.
        :rtype: tuple[int, int, int, int]
        """
        h, s, l = ColorConv.rgb_to_hsl(*self.rgb[:3])
        return ColorConv.base_1_to_255((h, s, l, self.__a))
    
    @hsl.setter
    def hsl(self, value: Tuple[float, ...]):
        """ Sets the color using normalized HSL values (0 to 1). Optionally includes an alpha component.
        
        :param value: A tuple of HSL values (h, s, l) with optional alpha (a), where 0 ≤ h, s, l ≤ 1 and 0 ≤ a ≤ 1.
        :type value: Tuple[float, ...]
        
        :raises AssertionError: If any of the HSL values or the alpha value (if provided) are out of bounds.
        """
        assert 0 <= value[0] <= 1 and 0 <= value[1] <= 1 and 0 <= value[2] <= 1, \
            "HSL values must be between 0 and 1"
            
        if len(value) > 3:
            assert 0 <= value[3] <= 1, "Alpha value must be between 0 and 1"
            self.__a = value[3]
            
        self.__r, self.__g, self.__b, self.__a = ColorConv.clamp_to_255_res(list(ColorConv.hsl_to_rgb(*value[:3])) + [self.__a])

    @property
    def hex(self) -> str:
        """ Returns the color as a HEX string, without alpha """
        return ColorConv.rgb_to_hex(self.__r, self.__g, self.__b)

    @property
    def hexa(self) -> str:
        """ Returns the color as a HEX string, with alpha """
        return ColorConv.rgb_to_hex(self.__r, self.__g, self.__b, self.__a)

    @hex.setter
    def hex(self, value: str):
        """ Sets the color from a HEX string """
        self.rgb = ColorConv.hex_to_rgb(value)


    @property
    def r(self) -> float:
        """ Returns the red component of the color in normalized RGB format.

        :return: The red component (0 ≤ r ≤ 1).
        :rtype: float
        """
        return self.__r
    
    @r.setter
    def r(self, value: float):
        """ Sets the red component of the color in normalized RGB format.

        :param value: The red component (0 ≤ value ≤ 1).
        :type value: float

        :raises AssertionError: If the value is out of bounds.
        """
        assert 0 <= value <= 1, "Red value must be between 0 and 1"
        self.__r = round(value * 255) / 255
    
    @property
    def g(self) -> float:
        """ Returns the green component of the color in normalized RGB format.

        :return: The green component (0 ≤ g ≤ 1).
        :rtype: float
        """
        return self.__g
    
    @g.setter
    def g(self, value: float):
        """ Sets the green component of the color in normalized RGB format.

        :param value: The green component (0 ≤ value ≤ 1).
        :type value: float

        :raises AssertionError: If the value is out of bounds.
        """
        assert 0 <= value <= 1, "Green value must be between 0 and 1"
        self.__g = round(value * 255) / 255
    
    @property
    def b(self) -> float:
        """ Returns the blue component of the color in normalized RGB format.

        :return: The blue component (0 ≤ b ≤ 1).
        :rtype: float
        """
        return self.__b
    
    @b.setter
    def b(self, value: float):
        """ Sets the blue component of the color in normalized RGB format.

        :param value: The blue component (0 ≤ value ≤ 1).
        :type value: float

        :raises AssertionError: If the value is out of bounds.
        """
        assert 0 <= value <= 1, "Blue value must be between 0 and 1"
        self.__b = round(value * 255) / 255
    
    
    @property
    def h(self) -> float:
        """ Returns the hue component of the color in normalized HSL format.

        :return: The hue component (0 ≤ h ≤ 1).
        :rtype: float
        """
        return self.hsl[0]
    
    @h.setter
    def h(self, value: float):
        """ Sets the hue component of the color in normalized HSL format.

        :param value: The hue component (0 ≤ value ≤ 1).
        :type value: float

        :raises AssertionError: If the value is out of bounds.
        """
        assert 0 <= value <= 1, "Hue value must be between 0 and 1"
        hsl = self.hsl  # cache value
        self.rgb = ColorConv.hsl_to_rgb(value, hsl[1], hsl[2])
    
    @property
    def s(self) -> float:
        """ Returns the saturation component of the color in normalized HSL format.

        :return: The saturation component (0 ≤ s ≤ 1).
        :rtype: float
        """
        return self.hsl[1]
    
    @s.setter
    def s(self, value: float):
        """ Sets the saturation component of the color in normalized HSL format.

        :param value: The saturation component (0 ≤ value ≤ 1).
        :type value: float

        :raises AssertionError: If the value is out of bounds.
        """
        assert 0 <= value <= 1, "Saturation value must be between 0 and 1"
        hsl = self.hsl  # cache value
        self.rgb = ColorConv.hsl_to_rgb(hsl[0], value, hsl[2])
    
    @property
    def l(self) -> float:
        """ Returns the lightness component of the color in normalized HSL format.

        :return: The lightness component (0 ≤ l ≤ 1).
        :rtype: float
        """
        return self.hsl[2]
    
    @l.setter
    def l(self, value: float):
        """ Sets the lightness component of the color in normalized HSL format.

        :param value: The lightness component (0 ≤ value ≤ 1).
        :type value: float

        :raises AssertionError: If the value is out of bounds.
        """
        assert 0 <= value <= 1, "Lightness value must be between 0 and 1"
        hsl = self.hsl  # cache value
        self.rgb = ColorConv.hsl_to_rgb(hsl[0], hsl[1], value)
    
    
    @property
    def alpha(self) -> float:
        """ Returns the alpha (opacity) component of the color.

        :return: The alpha component (0 ≤ alpha ≤ 1).
        :rtype: float
        """
        return self.__a
    
    @alpha.setter
    def alpha(self, value: float):
        """ Sets the alpha (opacity) component of the color.

        :param value: The alpha component (0 ≤ value ≤ 1).
        :type value: float

        :raises AssertionError: If the value is out of bounds.
        """
        assert 0 <= value <= 1, "Alpha value must be between 0 and 1"
        self.__a = round(value * 255) / 255


    def darken(self, amount: float) -> "Color":
        """ Darkens the color by reducing the lightness in HSL space.

        Decreases the lightness value of the color, making it darker. The amount parameter controls
        how much the color is darkened. A value of 0 means no change, and a value of 1 will make
        the color completely black.

        :param amount: A float representing the amount to darken the color (0 ≤ amount ≤ 1).
        :type amount: float
        
        :return: The updated color object after darkening.
        :rtype: Color
        
        :raises AssertionError: If the amount is not between 0 and 1.
        """
        
        assert 0 <= amount <= 1, \
            "Amount must be between 0 and 1"
        
        h, s, l, a = self.hsl  # Get current HSL values
        new_l = max(0, l - (l * amount))  # Decrease lightness toward 0 (black)
        self.hsl = h, s, new_l, a  # Update color with the new lightness value
        return self

    def lighten(self, amount: float) -> "Color":
        """ Lightens the color by increasing the lightness in HSL space.

        Increases the lightness value of the color, making it lighter. The amount parameter controls
        how much the color is lightened. A value of 0 means no change, and a value of 1 will make
        the color completely white.

        :param amount: A float representing the amount to lighten the color (0 ≤ amount ≤ 1).
        :type amount: float
        
        :return: The updated color object after lightening.
        :rtype: Color
        
        :raises AssertionError: If the amount is not between 0 and 1.
        """
        
        assert 0 <= amount <= 1, \
            "Amount must be between 0 and 1"
        
        h, s, l, a = self.hsl  # Get current HSL values
        new_l = min(1, l + ((1 - l) * amount))  # Increase lightness toward 1 (white)
        self.hsl = h, s, new_l, a  # Update color with the new lightness value
        return self


    def copy(self) -> "Color":
        """ Creates and returns a deep copy of the current color object.

        :return: A new `Color` object that is a copy of the current instance.
        :rtype: Color
        """
        return copy.deepcopy(self)
    
    
    def diff(self, compare: "Color") -> float:
        """ Calculates the difference between this and another color as a float 
        Calculates the Euclidean distance between the two colors in HSL space
        
        Computes the Euclidean distance between the two colors in HSL space, giving a measure
        of their difference. A smaller value indicates that the colors are more similar,
        while a larger value indicates they are more different.

        :param compare: The color to compare with.
        :type compare: Color
        
        :return: A float representing the Euclidean distance (color difference) between the two colors.
        :rtype: float
        
        :raises AssertionError: If the comparison object is not of the `Color` class.
        """
        
        assert isinstance(compare, __class__), "Invalid class comparison"

        h1, s1, l1, _ = self.hsl
        h2, s2, l2, _ = compare.hsl

        return math.sqrt(
            ((h1 - h2) ** 2) * 2 + # bias towards hue
             (s1 - s2) ** 2 +
            (l1 - l2) ** 2
        )
    
    
    def __str__(self):
        """ Returns a string representation of the color in RGB format.

        The string is formatted as 'r,g,b,a' where each component is a float between 0 and 1.

        :return: A string representing the color in RGB format.
        :rtype: str
        """
        return f"{self.__r},{self.__g},{self.__b},{self.__a}"

    def __repr__(self):
        """ Returns a string representation of the color in a more readable RGB format.

        The string is formatted as 'RGB r,g,b' where each component is a rounded float (up to 3 decimal places).

        :return: A string representing the color in RGB format for debugging and inspection.
        :rtype: str
        """
        return f"RGB {round(self.__r, 3)},{round(self.__g, 3)},{round(self.__b, 3)}"

    def __iter__(self) -> iter:
        """ Returns an iterator for the color components (r, g, b, a).

        :return: An iterator over the RGB components and alpha value of the color.
        :rtype: iter
        """
        return iter([self.__r, self.__g, self.__b, self.__a])
    
    def __eq__(self, compare: "Color"):
        """ Checks if the current color is equal to another color.

        This method compares the RGBA values of the two colors to determine equality.

        :param compare: The color to compare with.
        :type compare: Color
        
        :return: True if the colors are the same, False otherwise.
        :rtype: bool
        """
        if isinstance(compare, __class__):
            return self.rgb == compare.rgb
        return


TRANSPARENT:Color = Color((0, 0, 0, 0))
BLACK:Color = Color((0, 0, 0, 1))

LEGO_COLORS_DICT = {
    "white": [
        1,
        Color("#ffffff", _as=ColorMode.HEX),
    ],
    "grey": [
        2,
        Color("#DDDEDD", _as=ColorMode.HEX),
    ],
    "brick yellow": [
        5,
        Color("#D9BB7B", _as=ColorMode.HEX),
    ],
    "nougat": [
        18,
        Color("#D67240", _as=ColorMode.HEX),
    ],
    "bright red": [
        21,
        Color("#ff0000", _as=ColorMode.HEX),
    ],
    "bright blue": [
        23,
        Color("#0000ff", _as=ColorMode.HEX),
    ],
    "bright yellow": [
        24,
        Color("#Ffff00", _as=ColorMode.HEX),
    ],
    "black": [
        26,
        Color("#000000", _as=ColorMode.HEX),
    ],
    "dark green": [
        28,
        Color("#009900", _as=ColorMode.HEX),
    ],
    "bright green": [
        37,
        Color("#00cc00", _as=ColorMode.HEX),
    ],
    "dark orange": [
        38,
        Color("#A83D15", _as=ColorMode.HEX),
    ],
    "medium blue": [
        102,
        Color("#478CC6", _as=ColorMode.HEX),
    ],
    "bright orange": [
        106,
        Color("#ff6600", _as=ColorMode.HEX),
    ],
    "bright bluish green": [
        107,
        Color("#059D9E", _as=ColorMode.HEX),
    ],
    "bright yellowish-green": [
        119,
        Color("#95B90B", _as=ColorMode.HEX),
    ],
    "bright reddish violet": [
        124,
        Color("#990066", _as=ColorMode.HEX),
    ],
    "sand blue": [
        135,
        Color("#5E748C", _as=ColorMode.HEX),
    ],
    "sand yellow": [
        138,
        Color("#8D7452", _as=ColorMode.HEX),
    ],
    "earth blue": [
        140,
        Color("#002541", _as=ColorMode.HEX),
    ],
    "earth green": [
        141,
        Color("#003300", _as=ColorMode.HEX),
    ],
    "sand green": [
        151,
        Color("#5F8265", _as=ColorMode.HEX),
    ],
    "dark red": [
        154,
        Color("#80081B", _as=ColorMode.HEX),
    ],
    "flame yellowish orange": [
        191,
        Color("#F49B00", _as=ColorMode.HEX),
    ],
    "reddish brown": [
        192,
        Color("#5B1C0C", _as=ColorMode.HEX),
    ],
    "medium stone grey": [
        194,
        Color("#9C9291", _as=ColorMode.HEX),
    ],
    "dark stone grey": [
        199,
        Color("#4C5156", _as=ColorMode.HEX),
    ],
    "light stone grey": [
        208,
        Color("#E4E4DA", _as=ColorMode.HEX),
    ],
    "light royal blue": [
        212,
        Color("#87C0EA", _as=ColorMode.HEX),
    ],
    "bright purple": [
        221,
        Color("#DE378B", _as=ColorMode.HEX),
    ],
    "light purple": [
        222,
        Color("#EE9DC3", _as=ColorMode.HEX),
    ],
    "cool yellow": [
        226,
        Color("#FFFF99", _as=ColorMode.HEX),
    ],
    "dark purple": [
        268,
        Color("#2C1577", _as=ColorMode.HEX),
    ],
    "light nougat": [
        283,
        Color("#F5C189", _as=ColorMode.HEX),
    ],
    "dark brown": [
        308,
        Color("#300F06", _as=ColorMode.HEX),
    ],
    "medium nougat": [
        312,
        Color("#AA7D55", _as=ColorMode.HEX),
    ],
    "dark azur": [
        321,
        Color("#469bc3", _as=ColorMode.HEX),
    ],
    "medium azur": [
        322,
        Color("#68c3e2", _as=ColorMode.HEX),
    ],
    "aqua": [
        323,
        Color("#d3f2ea", _as=ColorMode.HEX),
    ],
    "medium lavender": [
        324,
        Color("#a06eb9", _as=ColorMode.HEX),
    ],
    "lavender": [
        325,
        Color("#cda4de", _as=ColorMode.HEX),
    ],
    "white glow": [
        329,
        Color("#f5f3d7", _as=ColorMode.HEX),
    ],
    "spring yellowish green": [
        326,
        Color("#e2f99a", _as=ColorMode.HEX),
    ],
    "olive green": [
        330,
        Color("#77774E", _as=ColorMode.HEX),
    ],
    "medium-yellowish green": [
        331,
        Color("#96B93B", _as=ColorMode.HEX),
    ],
}


LEGO_COLORS_LIST = [
    Color((255, 255, 255), _as = ColorMode.RGB255),
    Color((221, 222, 221), _as = ColorMode.RGB255),
    Color((217, 187, 123), _as = ColorMode.RGB255),
    Color((214, 114, 64), _as = ColorMode.RGB255),
    Color((255, 0, 0), _as = ColorMode.RGB255),
    Color((0, 0, 255), _as = ColorMode.RGB255),
    Color((255, 255, 0), _as = ColorMode.RGB255),
    Color((0, 0, 0), _as = ColorMode.RGB255),
    Color((0, 153, 0), _as = ColorMode.RGB255),
    Color((0, 204, 0), _as = ColorMode.RGB255),
    Color((168, 61, 21), _as = ColorMode.RGB255),
    Color((71, 140, 198), _as = ColorMode.RGB255),
    Color((255, 102, 0), _as = ColorMode.RGB255),
    Color((5, 157, 158), _as = ColorMode.RGB255),
    Color((149, 185, 11), _as = ColorMode.RGB255),
    Color((153, 0, 102), _as = ColorMode.RGB255),
    Color((94, 116, 140), _as = ColorMode.RGB255),
    Color((141, 116, 82), _as = ColorMode.RGB255),
    Color((0, 37, 65), _as = ColorMode.RGB255),
    Color((0, 51, 0), _as = ColorMode.RGB255),
    Color((95, 130, 101), _as = ColorMode.RGB255),
    Color((128, 8, 27), _as = ColorMode.RGB255),
    Color((244, 155, 0), _as = ColorMode.RGB255),
    Color((91, 28, 12), _as = ColorMode.RGB255),
    Color((156, 146, 145), _as = ColorMode.RGB255),
    Color((76, 81, 86), _as = ColorMode.RGB255),
    Color((228, 228, 218), _as = ColorMode.RGB255),
    Color((135, 192, 234), _as = ColorMode.RGB255),
    Color((222, 55, 139), _as = ColorMode.RGB255),
    Color((238, 157, 195), _as = ColorMode.RGB255),
    Color((255, 255, 153), _as = ColorMode.RGB255),
    Color((44, 21, 119), _as = ColorMode.RGB255),
    Color((245, 193, 137), _as = ColorMode.RGB255),
    Color((48, 15, 6), _as = ColorMode.RGB255),
    Color((170, 125, 85), _as = ColorMode.RGB255),
    Color((70, 155, 195), _as = ColorMode.RGB255),
    Color((104, 195, 226), _as = ColorMode.RGB255),
    Color((211, 242, 234), _as = ColorMode.RGB255),
    Color((160, 110, 185), _as = ColorMode.RGB255),
    Color((205, 164, 222), _as = ColorMode.RGB255),
    Color((245, 243, 215), _as = ColorMode.RGB255),
    Color((226, 249, 154), _as = ColorMode.RGB255),
    Color((119, 119, 78), _as = ColorMode.RGB255),
    Color((150, 185, 59), _as = ColorMode.RGB255),
]