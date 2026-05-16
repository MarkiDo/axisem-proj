import instaseis
import matplotlib.pyplot as plt
import numpy as np
from obspy import UTCDateTime

db = instaseis.open_db('../axisem/runs/MARS/')
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

st = db.get_seismograms(source=source,receiver=receiver,components='ZNE',kind='displacement')
for tr in st:
    tr.stats.starttime = origin
    print(tr)

print(st.plot())
st.write('TAYAK_modified_1s_DISP.mseed',format='mseed')