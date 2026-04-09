#!/usr/bin/env python3

'''
For an SWMF magnetometer file, obtain the corresponding observations from
SuperMAG and create validation metrics as a saved table.
'''

import os
import datetime as dt
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import numpy as np
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
parser.add_argument("-d", "--debug", default=False, action='store_true',
                    help="Turn on debugging mode.")
parser.add_argument("-u", "--user", type=str, default='dwelling',
                    help="Set the SuperMAG user name for downloading data.")
args = parser.parse_args()

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
    print(f'Start and end time: \n\t{tstart}\n\t{tend}')
    print(f'Mag list: {stats}')

# Fetch data:
allobs = {}
for s in stats:
    allobs[s] = fetch_mag(tstart, tend, args.user, s)
# --if it exists in backup folder, use it as-is.
# --Else, download fresh.



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