import instaseis
import matplotlib.pyplot as plt
import numpy as np
import os
from obspy import UTCDateTime
from obspy.signal.filter import bandpass
from real_data import load_real_zne

_here = os.path.dirname(os.path.abspath(__file__))
db = instaseis.open_db(os.path.join(_here, '..', 'axisem', 'SOLVER', 'mars'))
print(db)

FREQMIN = 0.1
FREQMAX = 1.0
CORNERS = 4
CHANNELS = ('BHU', 'BHV', 'BHW')

origin = UTCDateTime('2022-05-04 23:23:07')

stla = 4.502
stlo = 135.62
evlo = 171.9
evla = -3.0
evdp = 22.0
evdp_m = evdp*1000.

source = instaseis.Source.from_strike_dip_rake(latitude=evla,longitude=evlo,depth_in_m=evdp_m,strike=48,dip=43,rake=92,M0=5e15)
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
    ref_times = None

    for ax, comp in zip(axes, components):
        tr = st.select(component=comp)[0]
        times = tr.times(reftime=origin)
        if ref_times is None:
            ref_times = times

        if show_synthetic:
            syn_label = f'Synthetic (shift={SYNTHETIC_TIME_SHIFT:+.1f}s)' if SYNTHETIC_TIME_SHIFT else 'Synthetic'
            ax.plot(times + SYNTHETIC_TIME_SHIFT, tr.data * 1e9, color='black', linewidth=0.8, label=syn_label)

        if show_real and real is not None:
            t_real, d_real = real[comp]
            ax.plot(t_real, d_real * 1e9, color='red', linewidth=0.8, alpha=0.7, label='Observed')

        ax.set_ylabel(f'{comp}\n(nm)', fontsize=10)
        ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(ref_times[0], ref_times[-1])
        ax.legend(loc='upper right', fontsize=8)

    axes[-1].set_xlabel('Time relative to origin (s)', fontsize=10)
    fig.suptitle(
        f'InSight ELYSE — Mars S1222a  |  {origin.strftime("%Y-%m-%d %H:%M:%S")} UTC\n'
        f'Strike/Dip/Rake: 48/43/92  |  Depth: {evdp} km  |  Model1'
        + (f'  |  {title_suffix}' if title_suffix else ''),
        fontsize=11
    )
    fig.tight_layout()
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