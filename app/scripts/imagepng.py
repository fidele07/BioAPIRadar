import numpy as np
import io
import base64
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
from .util import pretty
from .colorbar import format_ColorScale, colorRampPalette

plt.switch_backend('Agg')

def create_imagePng(data,
                    breaks=None,
                    colors=None,
                    color_name='rainbow'):
    if len(data['lon'].shape) == 1:
        lon, lat = np.meshgrid(data['lon'], data['lat'])
    else:
        lon = data['lon']
        lat = data['lat']
    data = np.squeeze(data['data'])

    if hasattr(data, 'mask'):
        zmin = np.ma.min(data)
        zmax = np.ma.max(data)
    else:
        zmin = np.nanmin(data)
        zmax = np.nanmax(data)

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

    data = np.ma.masked_invalid(data)

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

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png',
                bbox_inches=None,
                transparent=True)
    img_buf.seek(0)
    img_png = base64.b64encode(img_buf.getvalue()).decode()
    img_png = f'data:image/png;base64,{img_png}'
    img_out = {'png': img_png, 'bounds': bounds}
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

def vcross_imagePng(vcross, color_name='rainbow'):
    dist = np.array(vcross['xaxis']['values'], dtype=float)
    hgt = np.array(vcross['yaxis']['values'], dtype=float)
    data = np.array(vcross['vcross'], dtype=float)
    data = np.ma.masked_invalid(data)

    fig, ax = plt.subplots(figsize=(10, 8))
    cs = ax.contourf(dist, hgt, data, levels=20, cmap=color_name)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='2%', pad=0.05)
    cbar = plt.colorbar(cs, cax=cax)
    cbar.set_label(f"{vcross['info']['name']} ({vcross['info']['units']})")
    ax.set_xlabel(vcross['xaxis']['label'])
    ax.set_ylabel(vcross['yaxis']['label'])
    ax.set_title(f"Vertical cross section of {vcross['info']['name']}")

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png',
                bbox_inches=None,
                transparent=True)
    img_buf.seek(0)
    img_png = base64.b64encode(img_buf.getvalue()).decode()
    img_png = f'data:image/png;base64,{img_png}'
    plt.close('all')

    return img_png

def bioclass_imagePng(data, color_0='red', color_1='blue'):
    if len(data['lon'].shape) == 1:
        lon, lat = np.meshgrid(data['lon'], data['lat'])
    else:
        lon = data['lon']
        lat = data['lat']
    data = np.squeeze(data['data'])
    data = np.ma.masked_invalid(data)

    cmap = mcolors.ListedColormap([color_0, color_1])
    norm = mcolors.BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)

    fig = plt.figure()
    ax = plt.axes([0, 0, 1, 1])
    pm = ax.pcolormesh(lon, lat, data,
                       shading='nearest')
    pm.set_cmap(cmap)
    pm.set_norm(norm)
    bbox = plt.axis('off')
    bounds = [[bbox[3].item(), bbox[0].item()],
              [bbox[2].item(), bbox[1].item()]]

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png',
                bbox_inches=None,
                transparent=True)
    img_buf.seek(0)
    img_png = base64.b64encode(img_buf.getvalue()).decode()
    img_png = f'data:image/png;base64,{img_png}'
    img_out = {'png': img_png, 'bounds': bounds}
    plt.close('all')

    return img_out

def vbioclass_imagePng(vcross, color_0='red', color_1='blue'):
    dist = np.array(vcross['xaxis']['values'], dtype=float)
    hgt = np.array(vcross['yaxis']['values'], dtype=float)
    data = np.array(vcross['vcross'], dtype=float)
    data = np.ma.masked_invalid(data)

    cmap = mcolors.ListedColormap([color_0, color_1])
    norm = mcolors.BoundaryNorm([-0.5, 0.5, 1.5], cmap.N)

    fig, ax = plt.subplots(figsize=(10, 8))
    pm = ax.pcolormesh(dist, hgt, data,
                       cmap=cmap, norm=norm,
                       shading='nearest'
                       )
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='2%', pad=0.05)
    cbar = plt.colorbar(pm, ticks=[0, 1], cax=cax)
    # cbar.set_label(vcross['info']['name'])
    cbar.ax.set_yticklabels(
        vcross['info']['category'], rotation=90, va='center'
    )
    ax.set_xlabel(vcross['xaxis']['label'])
    ax.set_ylabel(vcross['yaxis']['label'])
    ax.set_title(
        f"Vertical cross section of\n{vcross['info']['name']}"
    )
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png',
                bbox_inches=None,
                transparent=True)
    img_buf.seek(0)
    img_png = base64.b64encode(img_buf.getvalue()).decode()
    img_png = f'data:image/png;base64,{img_png}'
    plt.close('all')

    return img_png
