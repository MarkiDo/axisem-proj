import instaseis
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import numpy as np
import os
from obspy import UTCDateTime
from obspy.signal.filter import bandpass
from real_data import load_real_zne

_here = os.path.dirname(os.path.abspath(__file__))
db = instaseis.open_db(os.path.join(_here, '..', 'axisem', 'SOLVER', 'model_155_30'))
print(db)

FREQMIN = 0.01   # period 100s
FREQMAX = 0.0333 # period 30s (mesh's dominant period)
CORNERS = 4
CHANNELS = ('BHU', 'BHV', 'BHW')

origin = UTCDateTime('2022-05-04 23:23:07')

stla = 4.502
stlo = 135.62
evlo = 165.86
evla = 3.39
evdp = 30.0
evdp_m = evdp*1000.
dip = 197
strike = 24
rake = -68
M0 = 1e15

source = instaseis.Source.from_strike_dip_rake(latitude=evla,longitude=evlo,depth_in_m=evdp_m,strike=strike,dip=dip,rake=rake,M0=M0)
receiver = instaseis.Receiver(latitude=stla,longitude=stlo,network='XB',station='ELYSE')

st = db.get_seismograms(source=source,receiver=receiver,components='ZNE',kind='displacement',dt=0.05)
for tr in st:
    tr.stats.starttime = origin
    print(tr)

st.filter("bandpass", freqmin=FREQMIN, freqmax=FREQMAX, corners=CORNERS, zerophase=True)
st.write('Model1_5s_DISP.mseed', format='mseed')

print("Downloading real InSight data…")
real = load_real_zne(origin, freqmin=FREQMIN, freqmax=FREQMAX, corners=CORNERS, channels=CHANNELS)
if real is None:
    print("Proceeding without real data.")

# 'combined' | 'synthetic' | 'real' | 'all'
PLOT_MODE = 'combined'

# Shift synthetic trace in time (seconds). Positive → later, negative → earlier.
SYNTHETIC_TIME_SHIFT = 0.0

components = ['Z', 'N', 'E']


def _make_figure(title_suffix, show_synthetic, show_real):
    fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)
    xlim = None

    dual_scale = show_synthetic and show_real and real is not None

    for ax, comp in zip(axes, components):
        tr = st.select(component=comp)[0]
        times = tr.times(reftime=origin)
        lines, labels = [], []

        if show_synthetic:
            syn_label = f'Synthetic (shift={SYNTHETIC_TIME_SHIFT:+.1f}s)' if SYNTHETIC_TIME_SHIFT else 'Synthetic'
            ln, = ax.plot(times + SYNTHETIC_TIME_SHIFT, tr.data * 1e9, color='black', linewidth=0.8, label=syn_label)
            lines.append(ln)
            labels.append(syn_label)
            syn_span = (times[0] + SYNTHETIC_TIME_SHIFT, times[-1] + SYNTHETIC_TIME_SHIFT)
            xlim = syn_span if xlim is None else (min(xlim[0], syn_span[0]), max(xlim[1], syn_span[1]))
            if dual_scale:
                ax.tick_params(axis='y', labelcolor='black')

        if show_real and real is not None:
            t_real, d_real = real[comp]
            # Real amplitudes can be orders of magnitude larger than the synthetic's,
            # so give it its own y-axis to keep waveform shape/timing comparable.
            real_ax = ax.twinx() if dual_scale else ax
            ln, = real_ax.plot(t_real, d_real * 1e9, color='red', linewidth=0.8, alpha=0.7, label='Observed')
            lines.append(ln)
            labels.append('Observed')
            real_span = (t_real[0], t_real[-1])
            xlim = real_span if xlim is None else (min(xlim[0], real_span[0]), max(xlim[1], real_span[1]))
            if dual_scale:
                real_ax.tick_params(axis='y', labelcolor='red')
                real_ax.set_ylabel('Observed (nm)', fontsize=9, color='red')

        ax.set_ylabel(f'{comp}\n(nm)', fontsize=10)
        ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(*xlim)
        ax.legend(lines, labels, loc='upper right', fontsize=8)

    axes[-1].set_xlabel('Time relative to origin (s)', fontsize=10)
    fig.suptitle(
        f'InSight ELYSE — Mars S1222a  |  {origin.strftime("%Y-%m-%d %H:%M:%S")} UTC\n'
        f'Strike/Dip/Rake: {strike}/{dip}/{rake}  |  Depth: {evdp} km  |  Model1'
        + (f'  |  {title_suffix}' if title_suffix else ''),
        fontsize=11
    )
    fig.tight_layout()

    # Drag-select a region on any subplot to zoom the (shared) time axis in;
    # double-click anywhere on the figure to reset back to the full view.
    full_xlim = xlim

    def _on_select(xmin, xmax):
        if xmin == xmax:
            return
        axes[-1].set_xlim(xmin, xmax)
        fig.canvas.draw_idle()

    def _on_click(event):
        if event.dblclick:
            axes[-1].set_xlim(*full_xlim)
            fig.canvas.draw_idle()

    fig._span_selectors = [
        SpanSelector(ax, _on_select, 'horizontal', useblit=True,
                     props=dict(alpha=0.2, facecolor='tab:blue'))
        for ax in axes
    ]
    fig.canvas.mpl_connect('button_press_event', _on_click)

    return fig


def _save_and_show(fig, suffix=''):
    name = 'seismograms' + (f'_{suffix}' if suffix else '') + '.png'
    out = os.path.join(_here, name)
    fig.savefig(out, dpi=150)
    print(f'Saved: {out}')


modes = {
    'combined':  [('',          True,  True)],
    'synthetic': [('Synthetic', True,  False)],
    'real':      [('Observed',  False, True)],
    'all':       [('',          True,  True),
                  ('Synthetic', True,  False),
                  ('Observed',  False, True)],
}

for title_suffix, show_syn, show_real in modes[PLOT_MODE]:
    fig = _make_figure(title_suffix, show_syn, show_real)
    _save_and_show(fig, suffix=title_suffix.lower())

plt.show()