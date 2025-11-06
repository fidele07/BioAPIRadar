import numpy as np
import io
import base64
from tempfile import NamedTemporaryFile as tmpFile
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.animation as animation
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
        return None

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

    fig = plt.figure(dpi=dpi)
    ax = plt.axes([0, 0, 1, 1])
    mesh = ax.pcolormesh(
                lon, lat, data['frames'][0],
                vmin=vmin, vmax=vmax,
                shading='nearest'
            )
    mesh.set_cmap(cmap)
    mesh.set_norm(norm)
    bbox = plt.axis('off')
    bounds = [[bbox[3].item(), bbox[0].item()],
              [bbox[2].item(), bbox[1].item()]]
    txt = ax.text(
            0.01, 0.985, '',
            transform=ax.transAxes,
            ha='left', va='top',
            fontsize='xx-small', color='white',
            bbox=dict(
                    facecolor=(0, 0, 0, 0.35),
                    edgecolor='none', pad=2
                )
        )

    def format_time(t):
        if isinstance(t, (np.datetime64, )):
            t = t.astype('datetime64[s]').astype(object)
        if isinstance(t, datetime):
            return t.strftime("%Y-%m-%d %H:%M")
        return str(t)

    def update(i):
        mesh.set_array(data['frames'][i].ravel())
        txt.set_text(format_time(data['times'][i]))
        return (mesh, txt)

    anim = animation.FuncAnimation(
                fig, update,
                frames=len(data['frames']),
                blit=True, interval=400
            )

    with tmpFile(suffix='.gif', delete=False) as f:
        gif_file = f.name
    writer = animation.PillowWriter(
                fps=fps, metadata={'loop': 0}
            )
    anim.save(
        gif_file,
        writer=writer,
        dpi=dpi,
        savefig_kwargs={
            'transparent': True,
            'facecolor': 'none',
            'pad_inches': 0
        },
    )
    with open(gif_file, 'rb') as f:
        gif_bytes = f.read()

    img_gif = base64.b64encode(gif_bytes).decode('utf-8')
    img_gif = f'data:image/gif;base64,{img_gif}'
    img_out = {'gif': img_gif, 'bounds': bounds}
    plt.close('all')

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
    cbar.seek(0)
    cbar_png = base64.b64encode(cbar.getvalue()).decode()
    ckeys['png'] = f'data:image/png;base64,{cbar_png}'
    plt.close('all')

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

    fig = plt.figure()
    ax = plt.axes([0, 0, 1, 1])
    mesh = ax.pcolormesh(
            lon, lat, data['frames'][0],
            vmin=0, vmax=1, shading='nearest'
        )
    mesh.set_cmap(cmap)
    mesh.set_norm(norm)
    bbox = plt.axis('off')
    bounds = [[bbox[3].item(), bbox[0].item()],
              [bbox[2].item(), bbox[1].item()]]
    txt = ax.text(
            0.02, 0.95, '',
            transform=ax.transAxes,
            # ha='left', va='top',
            fontsize='xx-small', color='white',
            bbox=dict(
                    facecolor=(0, 0, 0, 0.4),
                    edgecolor='none', pad=2
                )
        )

    def format_time(t):
        if isinstance(t, (np.datetime64, )):
            t = t.astype('datetime64[s]').astype(object)
        if isinstance(t, datetime):
            return t.strftime("%Y-%m-%d %H:%M")
        return str(t)

    def init():
        mesh.set_array(data['frames'][0].ravel())
        txt.set_text(format_time(data['times'][0]))
        return (mesh, txt)

    # def update(i):
    #     print(i)
    #     # global mesh
    #     mesh.remove()
    #     mesh = ax.pcolormesh(
    #             lon, lat, data['frames'][i],
    #             vmin=0, vmax=1, shading='nearest'
    #         )
    #     mesh.set_cmap(cmap)
    #     mesh.set_norm(norm)
    #     txt.set_text(format_time(data['times'][i]))
    #     return (mesh, txt)

    def update(i):
        # print(i)
        mesh.set_array(data['frames'][i].ravel())
        txt.set_text(format_time(data['times'][i]))
        return (mesh, txt)

    anim = animation.FuncAnimation(
                fig, update, init_func=init,
                frames=len(data['frames']),
                blit=True, interval=400
            )

    # anim = animation.FuncAnimation(
    #             fig, update,
    #             frames=len(data['frames']),
    #             blit=False, interval=400
    #         )

    with tmpFile(suffix='.gif', delete=False) as f:
        gif_file = f.name
    writer = animation.PillowWriter(
                fps=fps, metadata={'loop': 0}
            )
    anim.save(
        gif_file,
        writer=writer,
        dpi=dpi,
        savefig_kwargs={
            'transparent': True,
            'facecolor': 'none',
            'pad_inches': 0
        },
    )
    with open(gif_file, 'rb') as f:
        gif_bytes = f.read()

    img_gif = base64.b64encode(gif_bytes).decode('utf-8')
    img_gif = f'data:image/gif;base64,{img_gif}'
    img_out = {'gif': img_gif, 'bounds': bounds}
    plt.close('all')

    return img_out
