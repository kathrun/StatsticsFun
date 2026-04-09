#!/usr/bin/env python3

'''
For an SWMF magnetometer file, obtain the corresponding observations from
SuperMAG and create validation metrics as a saved table.
'''

import os
import datetime as dt
import pickle
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import numpy as np
import matplotlib.pyplot as plt
from spacepy.plot import style, applySmartTimeTicks
from spacepy.pybats.bats import MagFile

import validator as vd
from supermag.supermag_api import fetch_mag

parser = ArgumentParser(description=__doc__,
                        formatter_class=RawDescriptionHelpFormatter)
parser.add_argument("mod", type=str, help="Path of SWMF model results " +
                    "'virtual magnetometer' file.")
parser.add_argument('-m', '--mags', type=str, default='all', help="Specify " +
                    "stations to use from SWMF file. Defaults to 'all', or " +
                    "all stations present in file. Example: MEA,HON")
parser.add_argument("--debug", default=False, action='store_true',
                    help="Turn on debugging mode.")
parser.add_argument("-u", "--user", type=str, default='dwelling',
                    help="Set the SuperMAG user name for downloading data.")
parser.add_argument("-o", "--outdir", type=str, default='metric_output/',
                    help="Set output directory for saving data.")
parser.add_argument("-d", "--data", type=str, default=None, help="Path to "+
                    "python pickle containing SuperMAG data.  If not given, " +
                    "data is downloaded via the SuperMAG web API.")
args = parser.parse_args()

# Hit 'em with that spacepy style:
style()

# Load SWMF file.
model = MagFile(args.mod)

# Get list of stations to use. Only keep stations that are in the SWMF file.
if args.mags == 'all':
    stats = model.attrs['namemag']
    # Remove DST from our model list.
    if 'DST' in stats:
        stats.pop(stats.index('DST'))
else:
    # Create a list of mags from the argument assuming a comma-separated list
    stats = []
    for s in args.mags.split(','):
        if s in model.attrs['namemag']:
            stats.append(s)
        elif args.debug:
            print(f'{s} not in SWMF output file. Skipping...')

# Get time period from file
tstart, tend = model['time'][0], model['time'][-1]

if args.debug:
    print(f'Working on file {args.mod}')
    print(f'Saving data to {args.outdir}')
    print(f'Start and end time: \n\t{tstart}\n\t{tend}')
    print(f'Mag list: {stats}')
    if args.data:
        print(f'Opening SuperMAG data from {args.data}')
    else:
        print('Fetching SuperMAG data from web...')

# Fetch data:
allobs, badstats = {}, []
if args.data:
    with open(args.data, 'rb') as f:
        allobs = pickle.load(f)
    for s in stats:
        if s not in allobs:
            badstats.append(s)
else:
    for s in stats:
        try:
            allobs[s] = fetch_mag(tstart, tend, args.user, s)
        except ValueError:  # Data not found? Remove from list!
            badstats.append(s)

# Clean up our station list:
for s in badstats:
    if args.debug:
        print(f'No data found for station {s}')
    stats.pop(stats.index(s))

# Calculate extra variables (e.g., dB/dt, H-component, etc.)
model.calc_h()
model.calc_dbdt()
for s in stats:
    # Helper var:
    mag = allobs[s]

    # Don't re-do things if already done in Pickle.
    if 'bh' in mag:
        continue

    # Observed H:
    mag['bh'] = np.sqrt(mag['nez'][:, 0]**2 + mag['nez'][:, 1]**2)

    # Observed dB/dt:
    # Helper vars:
    npts = mag['time'].size
    dtime = np.array([x.total_seconds() for x in np.diff(mag['time'])])
    dbn, dbe = np.zeros(npts), np.zeros(npts)

    # Central diff:
    dbn[1:-1] = (mag['nez'][2:, 0]-mag['nez'][:-2, 0]) /\
        (dtime[1:]+dtime[:-1])
    dbe[1:-1] = (mag['nez'][2:, 1]-mag['nez'][:-2, 1]) /\
        (dtime[1:]+dtime[:-1])
    # Forward diff:
    dbn[0] = (-mag['nez'][2, 0]+4*mag['nez'][1, 0]-3*mag['nez'][0, 0]) /\
        (dtime[1]+dtime[0])
    dbe[0] = (-mag['nez'][2, 1]+4*mag['nez'][1, 1]-3*mag['nez'][0, 1]) /\
        (dtime[1]+dtime[0])
    # Backward diff:
    dbn[-1] = (3*mag['nez'][-1, 0]-4*mag['nez'][-2, 0]+mag['nez'][-3, 0]) /\
        (dtime[-1]+dtime[-2])
    dbe[-1] = (3*mag['nez'][-1, 1]-4*mag['nez'][-2, 1]+mag['nez'][-3, 1]) /\
        (dtime[-1]+dtime[-2])

    # Store results:
    mag['dbxdt'] = dbn
    mag['dbydt'] = dbe

    # Create |dB/dt|_h:
    mag['dbhdt'] = np.sqrt(dbn**2 + dbe**2)

# Create folder for output.
if not os.path.exists(args.outdir):
    os.mkdir(args.outdir)

# Save our downloaded data:
with open(args.outdir + '/supermag_data.pkl', 'wb') as f:
    pickle.dump(allobs, f)

# Now, do validation!
for s in stats:
    # Helper vars:
    obs = allobs[s]
    mod = model[s]

    # Create comparison figure:
    fig, (a1, a2) = plt.subplots(2, 1, figsize=[10, 7], sharex=True)

    # Top row: compare DeltaB-H
    a1.plot(obs['time'], obs['bh'], label='Obs.', c='gray', alpha=.75)
    a1.plot(mod['time'], mod['dBh'], label='SWMF', c='C0')

    # Bottom row: compare dB-H/dt
    a2.plot(obs['time'], obs['dbhdt'], label='Obs.', c='gray', alpha=.75)
    a2.plot(mod['time'], mod['dBdth'], label='SWMF', c='C0', alpha=.75)

    # Prettify:
    a1.legend(loc='best')
    a1.set_title(f'Comparison to {s}')
    a1.set_ylabel(r'$\Delta B_H$ ($nT$)')
    a2.set_ylabel(r'$dB_H/dt$ ($nT/s$)')
    applySmartTimeTicks(a2, mod['time'], dolabel=True)
    fig.tight_layout()

    fig.savefig(args.outdir + f'/compare_{s}.png')
    if not plt.isinteractive():
        plt.close('all')

# mse = np.mean(np.square(obs['dBdt'] - mod['dBdt']))
#
# #print('MSE'=mse)
#
# '''
# Calculate RMSE
# '''
#
# rmse =  np.sqrt(np.mean((obs['dBdt']-mod['dBdt'])**2))
#
# # print('RMSE'=rmse)
#
# '''
# obs array is bigger than mod needs to be the same size to calculate values
# '''