from enum import Enum
import copy, math

class ColorConv():
    def rgb_to_hsl(r:float, g:float, b:float):
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


    def hsl_to_rgb(h:float, s:float, l:float):
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


    def base_255_to_1(color_iterable:list[int]) -> list[float]:
        return tuple(map(lambda x: x / 255, color_iterable))

    def base_1_to_255(color_iterable:list[float]) -> list[int]:
        return tuple(map(lambda x: round(x * 255), color_iterable))

    def clamp_to_255_res(color_iterable:list[float]) -> list[float]:
        return tuple(map(lambda x: round(x * 255) / 255, color_iterable))

class ColorMode(Enum):
    RGB = 0
    HSL = 1
    RGB255 = 2
    HSL255 = 3

class Color():
    def __init__(self, initial=None, _as:ColorMode = ColorMode.RGB):
        # Defaults to opaque black
        self.__r: float = 0.0
        self.__g: float = 0.0
        self.__b: float = 0.0
        self.__a: float = 1.0 
        
        if initial is not None:
            if type(initial) == __class__:
                self = initial
            
            else:
                assert type(initial) in [list, tuple] and 2 < len(initial) < 5, \
                    "Invalid initial format"
                
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
        return self.__r, self.__g, self.__b, self.__a
    
    @property
    def rgb255(self) -> tuple[float, float, float, float]:
        return ColorConv.base_1_to_255((self.__r, self.__g, self.__b, self.__a))
    
    @rgb.setter
    def rgb(self, value: tuple[float, float, float]):
        assert 0 <= value[0] <= 1 and 0 <= value[1] <= 1 and 0 <= value[2] <= 1, \
            "RGB values must be between 0 and 1"
        
        if len(value) > 3:
            assert 0 <= value[3] <= 1, "Alpha value must be between 0 and 1"
            self.__a = value[3]
        
        self.__r, self.__g, self.__b, self.__a = ColorConv.clamp_to_255_res(list(value[:3]) + [self.__a])


    @property
    def hsl(self) -> tuple[float, float, float, float]:
        h, s, l = ColorConv.rgb_to_hsl(*self.rgb[:3])
        return h, s, l, self.__a
    
    @property
    def hsl255(self) -> tuple[float, float, float, float]:
        h, s, l = ColorConv.rgb_to_hsl(*self.rgb[:3])
        return ColorConv.base_1_to_255((h, s, l, self.__a))
    
    @hsl.setter
    def hsl(self, value: tuple[float, float, float]):
        assert 0 <= value[0] <= 1 and 0 <= value[1] <= 1 and 0 <= value[2] <= 1, \
            "HSL values must be between 0 and 1"
            
        if len(value) > 3:
            assert 0 <= value[3] <= 1, "Alpha value must be between 0 and 1"
            self.__a = value[3]
            
        self.__r, self.__g, self.__b, self.__a = ColorConv.clamp_to_255_res(list(ColorConv.hsl_to_rgb(*value[:3])) + [self.__a])


    @property
    def r(self) -> float:
        return self.__r
    
    @r.setter
    def r(self, value: float):
        assert 0 <= value <= 1, "Red value must be between 0 and 1"
        self.__r = round(value * 255) / 255
    
    @property
    def g(self) -> float:
        return self.__g
    
    @g.setter
    def g(self, value: float):
        assert 0 <= value <= 1, "Green value must be between 0 and 1"
        self.__g = round(value * 255) / 255
    
    @property
    def b(self) -> float:
        return self.__b
    
    @b.setter
    def b(self, value: float):
        assert 0 <= value <= 1, "Blue value must be between 0 and 1"
        self.__b = round(value * 255) / 255
    
    
    @property
    def h(self) -> float:
        return self.hsl[0]
    
    @h.setter
    def h(self, value: float):
        assert 0 <= value <= 1, "Hue value must be between 0 and 1"
        hsl = self.hsl  # cache value
        self.rgb = ColorConv.hsl_to_rgb(value, hsl[1], hsl[2])
    
    @property
    def s(self) -> float:
        return self.hsl[1]
    
    @s.setter
    def s(self, value: float):
        assert 0 <= value <= 1, "Saturation value must be between 0 and 1"
        hsl = self.hsl  # cache value
        self.rgb = ColorConv.hsl_to_rgb(hsl[0], value, hsl[2])
    
    @property
    def l(self) -> float:
        return self.hsl[2]
    
    @l.setter
    def l(self, value: float):
        assert 0 <= value <= 1, "Lightness value must be between 0 and 1"
        hsl = self.hsl  # cache value
        self.rgb = ColorConv.hsl_to_rgb(hsl[0], hsl[1], value)
    
    
    @property
    def alpha(self) -> float:
        return self.__a
    
    @alpha.setter
    def alpha(self, value: float):
        assert 0 <= value <= 1, "Alpha value must be between 0 and 1"
        self.__a = round(value * 255) / 255


    def darken(self, amount: float):
        assert 0 <= amount <= 1, \
            "Amount must be between 0 and 1"
        
        h, s, l, a = self.hsl  # Get current HSL values
        new_l = max(0, l - (l * amount))  # Decrease lightness toward 0 (black)
        self.hsl = h, s, new_l, a  # Update color with the new lightness value
        return self

    def lighten(self, amount: float):
        assert 0 <= amount <= 1, \
            "Amount must be between 0 and 1"
        
        h, s, l, a = self.hsl  # Get current HSL values
        new_l = min(1, l + ((1 - l) * amount))  # Increase lightness toward 1 (white)
        self.hsl = h, s, new_l, a  # Update color with the new lightness value
        return self


    def copy(self):
        return copy.deepcopy(self)
    
    def diff(self, compare: "Color") -> float:
        """ Calculates the difference between this and another color as a float, using HSL """
        
        assert isinstance(compare, __class__), "Invalid class comparison"

        h1, s1, l1, _ = self.hsl
        h2, s2, l2, _ = compare.hsl

        return math.sqrt(
            ((h1 - h2) ** 2) * 2 + # bias towards hue
             (s1 - s2) ** 2 +
            (l1 - l2) ** 2
        )
    
    def __str__(self):
        return f"{self.__r},{self.__g},{self.__b},{self.__a}"

    def __repr__(self):
        return f"RGB {round(self.__r, 3)},{round(self.__g, 3)},{round(self.__b, 3)}"

    def __iter__(self):
        return iter([self.__r, self.__g, self.__b, self.__a])
    
    def __eq__(self, compare):
        if isinstance(compare, __class__):
            return self.rgb == compare.rgb
        return


TRANSPARENT:Color = Color((0, 0, 0, 0))
BLACK:Color = Color((0, 0, 0, 1))

LEGO_COLORS_DICT = {
    "white": [1, "#ffffff"],
    "grey": [2, "#DDDEDD"],
    "brick yellow": [5, "#D9BB7B"],
    "nougat": [18, "#D67240"],
    "bright red": [21, "#ff0000"],
    "bright blue": [23, "#0000ff"],
    "bright yellow": [24, "#Ffff00"],
    "black": [26, "#000000"],
    "dark green": [28, "#009900"],
    "bright green": [37, "#00cc00"],
    "dark orange": [38, "#A83D15"],
    "medium blue": [102, "#478CC6"],
    "bright orange": [106, "#ff6600"],
    "bright bluish green": [107, "#059D9E"],
    "bright yellowish-green": [119, "#95B90B"],
    "bright reddish violet": [124, "#990066"],
    "sand blue": [135, "#5E748C"],
    "sand yellow": [138, "#8D7452"],
    "earth blue": [140, "#002541"],
    "earth green": [141, "#003300"],
    "sand green": [151, "#5F8265"],
    "dark red": [154, "#80081B"],
    "flame yellowish orange": [191, "#F49B00"],
    "reddish brown": [192, "#5B1C0C"],
    "medium stone grey": [194, "#9C9291"],
    "dark stone grey": [199, "#4C5156"],
    "light stone grey": [208, "#E4E4DA"],
    "light royal blue": [212, "#87C0EA"],
    "bright purple": [221, "#DE378B"],
    "light purple": [222, "#EE9DC3"],
    "cool yellow": [226, "#FFFF99"],
    "dark purple": [268, "#2C1577"],
    "light nougat": [283, "#F5C189"],
    "dark brown": [308, "#300F06"],
    "medium nougat": [312, "#AA7D55"],
    "dark azur": [321, "#469bc3"],
    "medium azur": [322, "#68c3e2"],
    "aqua": [323, "#d3f2ea"],
    "medium lavender": [324, "#a06eb9"],
    "lavender": [325, "#cda4de"],
    "white glow": [329, "#f5f3d7"],
    "spring yellowish green": [326, "#e2f99a"],
    "olive green": [330, "#77774E"],
    "medium-yellowish green": [331, "#96B93B"],
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