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

# st.filter("bandpass", freqmin=0.1, freqmax=1.0, corners=3)
st.write('Model1_5s_DISP.mseed', format='mseed')

print("Downloading real InSight data…")
real = load_real_zne(origin)
if real is None:
    print("Proceeding without real data.")

components = ['Z', 'N', 'E']
fig, axes = plt.subplots(3, 1, figsize=(12, 7), sharex=True)

for ax, comp in zip(axes, components):
    tr = st.select(component=comp)[0]
    times = tr.times(reftime=origin)
    ax.plot(times, tr.data * 1e9, color='black', linewidth=0.8, label='Synthetic')

    if real is not None:
        t_real, d_real = real[comp]
        ax.plot(t_real, d_real * 1e9, color='red', linewidth=0.8, alpha=0.7, label='Observed')

    ax.set_ylabel(f'{comp}\n(nm)', fontsize=10)
    ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(times[0], times[-1])
    ax.legend(loc='upper right', fontsize=8)

axes[-1].set_xlabel('Time relative to origin (s)', fontsize=10)
fig.suptitle(
    f'InSight ELYSE — Mars S1222a  |  {origin.strftime("%Y-%m-%d %H:%M:%S")} UTC\n'
    f'Strike/Dip/Rake: 48/43/92  |  Depth: {evdp} km  |  Model1',
    fontsize=11
)
fig.tight_layout()

out = os.path.join(_here, 'seismograms.png')
fig.savefig(out, dpi=150)
print(f'Saved: {out}')
plt.show()