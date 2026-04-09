'''
Attmept at creating a linear regression analysis script for quick model validation for any event.
'''
import os
import numpy as np
import datetime as dt
import validator as vd

def read_obs(filename):
    '''
    Read mag file and create arrays with each variable.
    TO-DO 
    - Pull mag files directly from supermag

    Parameters
    ==========
    filename : string
       Path to the file to open and parse.

    Returns
    =======
    data : dict
       A dictionary containing numpy arrays of the values in the file,
       including "time", "bx", "by", "bz", and "dBdt".

    Examples
    ========
    >>> data = read_mag('data/ott_obs.txt')
    >>> data['time']
    '''

    with open(filename, 'r') as f:
        # Skip header lines.
        trash = 'garbage'
        while '[year]' not in trash:
            trash = f.readline()
        # Slurp in remaning lines:
        lines = f.readlines()

    # Count lines, produce empty container.
    nLines = len(lines)
    data = {'time': np.zeros(nLines, dtype=object)}
    for v in ['bx', 'by', 'bz']:
        data[v] = np.zeros(nLines)

    # Now, loop through dem lines:
    for i, line in enumerate(lines):
        # Break into parts:
        parts = line.split()

        # Extract and convert time:
        t_raw = '_'.join(parts[:6])
        data['time'][i] = dt.datetime.strptime(
            t_raw, '%Y_%m_%d_%H_%M_%S')

        # Extract values:
        for v, x in zip(['bx', 'by', 'bz'], parts[-3:]):
            data[v][i] = x

    # Calculate time derivatives.  Follow the forward difference
    # method and definition of dB_H used in Pulkkinen et al. 2013.
    # Get dt values:
    dt = np.array([x.total_seconds() for x in np.diff(data['time'])])

    # Loop through variables.  Start by
    data['dBdt'] = np.sqrt((data['bx'][1:] - data['bx'][:-1])**2 +
                           (data['by'][1:] - data['by'][:-1])**2) / dt

    return data

'''
Set model array to same datetime size as observation file. 
'''
data['time']

def read_mod(filename):
 with open(filename, 'r') as f:
        # Skip header lines.
        trash = 'garbage'
        while '[year]' not in trash:
            trash = f.readline()
        # Slurp in remaning lines:
        lines = f.readlines()

    # Count lines, produce empty container.
    nLines = len(lines)
    data = {'time': np.zeros(nLines, dtype=object)}
    for v in ['bx', 'by', 'bz']:
        data[v] = np.zeros(nLines)

    # Now, loop through dem lines:
    for i, line in enumerate(lines):
        # Break into parts:
        parts = line.split()

        # Extract and convert time:
        t_raw = '_'.join(parts[:6])
        data['time'][i] = dt.datetime.strptime(
            t_raw, '%Y_%m_%d_%H_%M_%S')

        # Extract values:
        for v, x in zip(['bx', 'by', 'bz'], parts[-3:]):
            data[v][i] = x

    # Calculate time derivatives.  Follow the forward difference
    # method and definition of dB_H used in Pulkkinen et al. 2013.
    # Get dt values:
    dt = np.array([x.total_seconds() for x in np.diff(data['time'])])

    # Loop through variables.  Start by
    data['dBdt'] = np.sqrt((data['bx'][1:] - data['bx'][:-1])**2 +
                           (data['by'][1:] - data['by'][:-1])**2) / dt

    return data



'''
Open test files. 
'''

obs = read_obs('tests/data/ott_obs.txt')
mod = read_mod('tests/data/ott_mod.txt')
'''
same array size?
'''
np

tlim = [dt.datetime(2003, 10, 29, 6, 0, 0),
        dt.datetime(2003, 10, 30, 6, 0, 0)]

'''
Calculate mean sq. error for each data point in each array.
'''

mse = np.mean(np.square(obs['dBdt'] - mod['dBdt']))

print('MSE'=mse)

'''
Calculate RMSE
'''

rmse =  np.sqrt(np.mean((obs['dBdt']-mod['dBdt'])**2))

print('RMSE'=rmse)

'''
obs array is bigger than mod needs to be the same size to calculate values
'''