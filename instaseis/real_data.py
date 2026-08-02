import io
import numpy as np
import requests
from obspy import read
from obspy.clients.fdsn import Client
from obspy.signal.filter import bandpass
from obspy.signal.rotate import rotate2zne


NET = 'XB'
STA = 'ELYSE'
LOC = '02'

DEFAULT_CHANNELS = ('BHU', 'BHV', 'BHW')
DEFAULT_FREQMIN = 0.1
DEFAULT_FREQMAX = 1.0
DEFAULT_CORNERS = 4


def _download_mseed(start, end, chan):
    url = (
        "https://service.iris.edu/fdsnws/dataselect/1/query?"
        f"net={NET}&sta={STA}&loc={LOC}&cha={chan}&"
        f"starttime={start.isoformat()}&endtime={end.isoformat()}&"
        "quality=M&format=miniseed&nodata=404"
    )
    r = requests.get(url, timeout=120)
    if r.status_code == 200:
        return read(io.BytesIO(r.content))
    print(f"Real data download failed: HTTP {r.status_code}")
    return None


def _get_inventory(t0, t1, chan):
    return Client("EARTHSCOPE").get_stations(
        network=NET, station=STA, location=LOC, channel=chan,
        starttime=t0, endtime=t1, level="response"
    )


def _azi_dip(inv, channel):
    c = inv.select(channel=channel, station=STA)[0][0][0]
    return c.azimuth, c.dip


def load_real_zne(origin, pre_event_s=300, post_event_s=3600,
                  freqmin=DEFAULT_FREQMIN, freqmax=DEFAULT_FREQMAX,
                  corners=DEFAULT_CORNERS, channels=DEFAULT_CHANNELS):
    """
    Download InSight VBB data around `origin`, rotate UVW→ZNE,
    remove instrument response (→ displacement), and bandpass-filter.

    Returns a dict {'Z': (times, data), 'N': ..., 'E': ...} with times
    in seconds relative to `origin`, or None on failure.
    """
    chan_U, chan_V, chan_W = channels
    chan_wildcard = chan_U[:2] + '*'

    raw = _download_mseed(origin - pre_event_s, origin + post_event_s, chan_wildcard)
    if raw is None:
        return None

    ts_U = raw.select(channel=chan_U)
    ts_V = raw.select(channel=chan_V)
    ts_W = raw.select(channel=chan_W)
    if not (ts_U and ts_V and ts_W):
        print(f"{chan_U}/{chan_V}/{chan_W} not found in downloaded data:", raw)
        return None

    # Synchronise time windows
    t0 = max(ts_U[0].stats.starttime, ts_V[0].stats.starttime, ts_W[0].stats.starttime)
    t1 = min(ts_U[0].stats.endtime,   ts_V[0].stats.endtime,   ts_W[0].stats.endtime)
    for s in [ts_U, ts_V, ts_W]:
        s.trim(t0, t1)
        s.detrend("linear")

    inv = _get_inventory(t0, t1, chan_wildcard)

    for s in [ts_U, ts_V, ts_W]:
        s.remove_response(inventory=inv, output="DISP",
                          zero_mean=True, taper=True, taper_fraction=0.05)

    U_azi, U_dip = _azi_dip(inv, chan_U)
    V_azi, V_dip = _azi_dip(inv, chan_V)
    W_azi, W_dip = _azi_dip(inv, chan_W)

    Z, N, E = rotate2zne(
        ts_U[0].data, U_azi, U_dip,
        ts_V[0].data, V_azi, V_dip,
        ts_W[0].data, W_azi, W_dip,
    )

    sr = ts_U[0].stats.sampling_rate
    Z_bp = bandpass(Z, freqmin, freqmax, sr, corners=corners, zerophase=True)
    N_bp = bandpass(N, freqmin, freqmax, sr, corners=corners, zerophase=True)
    E_bp = bandpass(E, freqmin, freqmax, sr, corners=corners, zerophase=True)

    times = np.arange(len(Z)) / sr + float(t0 - origin)

    return {'Z': (times, Z_bp), 'N': (times, N_bp), 'E': (times, E_bp)}
