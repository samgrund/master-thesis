import matplotlib.dates as mdates
from datetime import datetime, timedelta
import predict
import matplotlib.pyplot as plt
import numpy as np


def minute_timestamps(n_hours):
    """Returns a list of timestamps for the start of each minute for the next n hours"""
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=n_hours)
    timestamps = []
    current_time = start_time.replace(second=0, microsecond=0)
    while current_time < end_time:
        timestamps.append(current_time.timestamp())
        current_time += timedelta(minutes=1)
    return timestamps


def predict_many(tle, qth, timestamps):
    """Returns a list of predictions for the given timestamps"""
    predictions = []
    for timestamp in timestamps:
        predictions.append(predict.observe(tle, qth, timestamp))
    return predictions


def get_visible_passtimes(datetimes, predictions):
    """Returns a list of tuples of (start_time, end_time) for each pass"""
    visible_passtimes = []
    tstart = None
    tend = None
    for prediction in predictions:
        prediction['elevation'] = prediction['elevation'] + 40
    for (datetime, prediction) in zip(datetimes, predictions):
        if prediction['elevation'] > 0 and prediction['sunlit'] == 1:
            if tstart is None:
                tstart = datetime
        if prediction['elevation'] < 0 and prediction['sunlit'] == 1:
            if tstart is not None:
                tend = datetime
                visible_passtimes.append((tstart, tend))
                tstart = None
                tend = None
        if prediction['elevation'] > 0 and prediction['sunlit'] == 0:
            if tstart is not None:
                tend = datetime
                visible_passtimes.append((tstart, tend))
                tstart = None
                tend = None
        if prediction['elevation'] < 0 and prediction['sunlit'] == 0:
            if tstart is not None:
                tend = datetime
                visible_passtimes.append((tstart, tend))
                tstart = None
                tend = None
    if tstart is not None:
        tend = datetime
        visible_passtimes.append((tstart, tend))
    return visible_passtimes


def get_visible(tle, qth, tstamps, satname='Satellite'):
    tstamps = np.array(tstamps)
    datetimes = [datetime.fromtimestamp(tstamp) for tstamp in tstamps]
    predictions = predict_many(tle, qth, tstamps)
    passtimes = get_visible_passtimes(datetimes, predictions)

    pass_strings = []
    for (start, end) in passtimes:
        string = f'{start.strftime("%H:%M")} - {end.strftime("%H:%M")}'
        pass_strings.append(string)

    alts = np.array([p['elevation'] for p in predictions])
    sunlits = np.array([p['sunlit'] for p in predictions])
    visible_mask = np.where((alts > 0) & (sunlits == 1))

    fig, ax = plt.subplots(figsize=(7, 4), tight_layout=True)
    fig.suptitle(satname, fontsize=16)
    # Shade area where sunlits == 1
    ax.fill_between(datetimes, 0, alts, where=(sunlits == 1) & (
        alts <= 0), color='red', alpha=0.3, label='Sunlit (alt <= 0)')
    ax.fill_between(datetimes, 0, alts, where=(sunlits == 1) & (
        alts > 0), color='blue', alpha=0.3, label='Visible (alt > 0)')

    delta_t = datetimes[-1] - datetimes[0]
    x0 = datetimes[-1] + delta_t * 0.1
    y0 = np.mean(alts) * 1.5
    for pass_string in pass_strings:
        ax.text(x0, y0, pass_string, fontsize=15)
        y0 -= 10

    # Plot the visible times
    ax.plot(datetimes, alts, color='black', alpha=1, label='Elevation')
    ax.set_xlabel('Time [Current machine time zone]')
    ax.set_ylabel('Elevation (degrees)')
    ax.hlines(0, datetimes[0], datetimes[-1],
              linestyles='--', alpha=1, color='black')
    ax.grid(which='major', axis='x', linestyle='--', alpha=0.8)
    ax.legend(bbox_to_anchor=(1.02, 1), loc=2)
    try:
        ax.set_xticklabels(ax.get_xticks(), rotation=45)
    except UserWarning:
        pass
    date_fmt = '%H:%M'
    date_formatter = mdates.DateFormatter(date_fmt)
    ax.xaxis.set_major_formatter(date_formatter)
    plt.close(fig)
    return fig, passtimes
