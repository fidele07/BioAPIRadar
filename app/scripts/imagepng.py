import numpy as np
import io
import base64
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from .util import pretty
from .colorbar import format_ColorScale, colorRampPalette

plt.switch_backend('Agg')

def create_imagePng(data,
                    breaks=None,
                    colors=None,
                    color_name='rainbow'):
    lon, lat = np.meshgrid(data['lon'], data['lat'])
    data = np.squeeze(data['data'])

    if hasattr(data, 'mask'):
        zmin = np.ma.min(data)
        zmax = np.ma.max(data)
    else:
        zmin = np.nanmin(data)
        zmax = np.nanmax(data)

    if np.isnan(zmax):
        return None

    if breaks is None:
        if zmin == zmax:
            breaks = zmin + [-0.01, 0.01]
        else:
            breaks = pretty(zmin, zmax, 20)

    if colors is None:
        nkol = len(breaks) - 1
        listedCmap = plt.get_cmap(color_name, nkol)
        colors = [None] * nkol
        for j in range(nkol):
            colors[j] = mcolors.to_hex(listedCmap(j))

    ###### map
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(breaks, cmap.N)
    vmin = breaks[0]
    vmax = breaks[-1]

    fig = plt.figure()
    ax = plt.axes([0, 0, 1, 1])
    pm = ax.pcolormesh(lon, lat, data,
                       vmin=vmin, vmax=vmax,
                       shading='nearest')
    pm.set_cmap(cmap)
    pm.set_norm(norm)
    bbox = plt.axis('off')
    bounds = [[bbox[3].item(), bbox[0].item()],
              [bbox[2].item(), bbox[1].item()]]

    img = io.BytesIO()
    plt.savefig(img, format='png',
                bbox_inches=None,
                transparent=True)
    img.seek(0)
    img_png = base64.b64encode(img.getvalue()).decode()
    img_png = 'data:image/png;base64,' + img_png
    img_out = {'png': img_png, 'bounds': bounds}
    plt.close('all')

    ##### colorbar
    ckeys = format_ColorScale(breaks, colors)

    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(breaks, cmap.N)

    fig, ax = plt.subplots(figsize=(8, 1), layout='constrained')
    fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
                 cax=ax, extendrect=True, orientation='horizontal')

    cbar = io.BytesIO()
    plt.savefig(cbar, format='png',
                bbox_inches=None,
                transparent=True)
    cbar.seek(0)
    cbar_png = base64.b64encode(cbar.getvalue()).decode()
    ckeys['png'] = 'data:image/png;base64,' + cbar_png
    plt.close('all')

    return {'data': img_out, 'ckeys': ckeys}
