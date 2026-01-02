import numpy as np
import io
import base64
from PIL import Image
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from datetime import datetime
from .util import pretty
from .colorbar import format_ColorScale, colorRampPalette

plt.switch_backend('Agg')

def create_animeGif(data,
                    breaks=None,
                    colors=None,
                    color_name='rainbow',
                    dpi=150, fps=2):
    if len(data['lon'].shape) == 1:
        lon, lat = np.meshgrid(data['lon'], data['lat'])
    else:
        lon = data['lon']
        lat = data['lat']

    if hasattr(data['frames'], 'mask'):
        zmin = np.ma.min(data['frames'])
        zmax = np.ma.max(data['frames'])
    else:
        zmin = np.nanmin(data['frames'])
        zmax = np.nanmax(data['frames'])

    if np.isnan(zmax):
        zmin = -0.1
        zmax = 0.1

    if breaks is None:
        if zmin == zmax:
            breaks = zmin + [-0.01, 0.01]
        else:
            breaks = pretty(zmin, zmax, 20)

    nkol = len(breaks) - 1
    if colors is None:
        listedCmap = plt.get_cmap(color_name, nkol)
        colors = [None] * nkol
        for j in range(nkol):
            colors[j] = mcolors.to_hex(listedCmap(j))
    else:
        colors_fun = colorRampPalette(colors)
        colors = colors_fun(nkol)

    ###### map
    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(breaks, cmap.N)
    vmin = breaks[0]
    vmax = breaks[-1]

    def format_time(t):
        if isinstance(t, (np.datetime64, )):
            t = t.astype('datetime64[s]').astype(object)
        if isinstance(t, datetime):
            return t.strftime("%Y-%m-%d %H:%M")
        return str(t)

    data['frames'] = np.ma.masked_invalid(data['frames'])

    imgs = []
    bounds = None

    for i in range(len(data['frames'])):
        fig = plt.figure(dpi=dpi)
        ax = plt.axes([0, 0, 1, 1])
        mesh = ax.pcolormesh(
                    lon, lat, data['frames'][i],
                    vmin=vmin, vmax=vmax,
                    shading='nearest'
                )
        mesh.set_cmap(cmap)
        mesh.set_norm(norm)
        bbox = plt.axis('off')
        if bounds is None:
            bounds = [[bbox[3].item(), bbox[0].item()],
                      [bbox[2].item(), bbox[1].item()]]
        txt = ax.text(
                0.01, 0.985,
                format_time(data['times'][i]),
                transform=ax.transAxes,
                ha='left', va='top',
                fontsize=8, color='white',
                bbox=dict(
                        facecolor=(0, 0, 0, 0.35),
                        edgecolor='none', pad=2
                    )
            )
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png',
                    bbox_inches=None,
                    transparent=True)
        plt.close(fig)
        img_buf.seek(0)
        imgs.append(
                Image.open(img_buf).convert('RGBA')
            )

    buf_gif = io.BytesIO()
    imgs[0].save(
        buf_gif,
        format='GIF',
        save_all=True,
        append_images=imgs[1:],
        duration=400,
        loop=0,
        transparency=0,
        disposal=2,
    )
    buf_gif.seek(0)

    img_gif = base64.b64encode(buf_gif.read()).decode('utf-8')
    img_gif = f'data:image/gif;base64,{img_gif}'
    img_out = {'gif': img_gif, 'bounds': bounds}

    ##### colorbar
    ckeys = format_ColorScale(breaks, colors)

    cmap = mcolors.ListedColormap(colors)
    norm = mcolors.BoundaryNorm(breaks, cmap.N)

    fig, ax = plt.subplots(figsize=(8, 1), layout='constrained')
    fig.colorbar(
            mpl.cm.ScalarMappable(norm=norm, cmap=cmap),
            cax=ax, extendrect=True,
            orientation='horizontal'
        )

    cbar = io.BytesIO()
    plt.savefig(
            cbar, format='png',
            bbox_inches=None,
            transparent=True
        )
    plt.close(fig)
    cbar.seek(0)
    cbar_png = base64.b64encode(cbar.getvalue()).decode()
    ckeys['png'] = f'data:image/png;base64,{cbar_png}'

    return {'data': img_out, 'ckeys': ckeys}

def bioclass_animeGif(data,
                     color_0='red',
                     color_1='blue',
                     dpi=150, fps=2):
    if len(data['lon'].shape) == 1:
        lon, lat = np.meshgrid(data['lon'], data['lat'])
    else:
        lon = data['lon']
        lat = data['lat']

    cmap = mcolors.ListedColormap([color_0, color_1])
    norm = mcolors.BoundaryNorm([0, 1], cmap.N)

    def format_time(t):
        if isinstance(t, (np.datetime64, )):
            t = t.astype('datetime64[s]').astype(object)
        if isinstance(t, datetime):
            return t.strftime("%Y-%m-%d %H:%M")
        return str(t)

    imgs = []
    bounds = None

    for i in range(len(data['frames'])):
        fig = plt.figure()
        ax = plt.axes([0, 0, 1, 1])
        mesh = ax.pcolormesh(
                lon, lat, data['frames'][i],
                vmin=0, vmax=1, shading='nearest'
            )
        mesh.set_cmap(cmap)
        mesh.set_norm(norm)
        bbox = plt.axis('off')
        if bounds is None:
            bounds = [[bbox[3].item(), bbox[0].item()],
                      [bbox[2].item(), bbox[1].item()]]
        txt = ax.text(
                0.02, 0.95, 
                format_time(data['times'][i]),
                transform=ax.transAxes,
                ha='left', va='top',
                fontsize=8, color='white',
                bbox=dict(
                        facecolor=(0, 0, 0, 0.4),
                        edgecolor='none', pad=2
                    )
            )
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png',
                    bbox_inches=None,
                    transparent=True)
        plt.close(fig)
        img_buf.seek(0)
        imgs.append(
                Image.open(img_buf).convert('RGBA')
            )

    buf_gif = io.BytesIO()
    imgs[0].save(
        buf_gif,
        format='GIF',
        save_all=True,
        append_images=imgs[1:],
        duration=400,
        loop=0,
        transparency=0,
        disposal=2,
    )
    buf_gif.seek(0)

    img_gif = base64.b64encode(buf_gif.read()).decode('utf-8')
    img_gif = f'data:image/gif;base64,{img_gif}'
    img_out = {'gif': img_gif, 'bounds': bounds}

    return img_out
