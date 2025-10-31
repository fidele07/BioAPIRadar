import numpy as np
import re
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
plt.switch_backend('Agg')

def colorRampPalette(colors):
    rgbs = [mcolors.to_rgb(c) for c in colors]
    nc = len(rgbs)

    if nc == 1:
        rgbs = [rgbs[0], rgbs[0]]
        nc = 2

    x = np.linspace(0, 1, nc)
    palette = (interp1d(x, np.array([rgbs[i][0] for i in range(nc)])),
               interp1d(x, np.array([rgbs[i][1] for i in range(nc)])),
               interp1d(x, np.array([rgbs[i][2] for i in range(nc)])))

    def roundcolor(cl):
        return np.array([max(min(1.0, e), 0) for e in cl])

    def ramp(n):
        x = np.linspace(0, 1, n)
        rgb = (roundcolor(palette[0](x)),
               roundcolor(palette[1](x)),
               roundcolor(palette[2](x)))
        kol = []
        for j in range(n):
            kl = (rgb[0][j], rgb[1][j], rgb[2][j])
            kol = kol + [mcolors.rgb2hex(kl)]
        return kol

    return ramp

def format_ColorScale(breaks, colors, colors_ext=None):
    kol = colors
    if colors_ext is not None:
        kol = [None] * (len(colors) + 2)
        for j in range(len(kol)):
            if j == 0:
                kol[j] = colors_ext[0]
            elif j == len(kol) - 1:
                kol[j] = colors_ext[1]
            else:
                kol[j] = colors[j - 1]
        
    breaks = [str(round(x, 4)) for x in breaks]

    return {'labels': breaks, 'colors': kol}

def get_ColorBarName(color, n, inverse=False):
    if n < 4:
        raise Exception(f'n must be greater than 3')
    listedCmap = plt.get_cmap(color, n)
    kolor = [None] * n
    for j in range(n):
        kolor[j] = mcolors.to_hex(listedCmap(j))

    if inverse:
        kolor.reverse()

    return {
        'colors': kolor[1:-1],
        'ext': [kolor[0], kolor[-1]]
    }

def convert_NameToHex(color_list):
    return [mcolors.to_hex(c) for c in color_list]
