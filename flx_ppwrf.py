#!/usr/bin/env python
# This script will accept a set of wrfout files
# as arguments and replace the accumulated precip
# with hourly precipitation data.  The input files
# be on the format one file and output time per hour.
#
# Usage: (if put in $PATH)
#   ppwrf_hourly_precip.py ./wrfout_d01_*
#
# If ./ contains N files matching 'wrfout_d01_*' then
# the result will be N-1 files named 'pwrfout_d01_*'
# the first of these will have the same output time as
# the second file in the original list.

#-------------------------------------------------------------------------------

from sys import argv        # support CLI arguments
#from shutil import copyfile # For creating the output netCDF
from numpy import *         # Numeric module
from pycdf import *         # NetCDF module

# The pycdf module was chosen due to it's support for
# modifying existing netCDF files which makes the addition
# of a single record variable easier. (We don't need to
# copy the entire file variable by variable)

# pycdf can be installed with support for different numeric modules
# I used numpy because I'm used to it and I have it installed.
# If one wants to use a different numeric module the pycdf package
# has to be reinstalled. (Or one could use both packages but that's
# just messy)

#-------------------------------------------------------------------------------

# The problem:
#   WRF outputs accumulated precipiation, we want hourly
# The solution:
#   We subtract acc rain of the previous output time
#   from the current output time

# Setup 2 file lists
fn_previous   = argv[1:-1]    # Previous files
fn_current    = argv[2:]    # Current files

# Variables we should use for calculating total hourly precipitation:
vnames  = ['RAINC','RAINSH','RAINNC','SNOWNC','GRAUPELNC','HAILNC','asdaa']

# String to be appended to the each variable description
sdescr = ', SINCE LAST OUTPUT TIME'

for fn_p,fn_c in zip(fn_previous,fn_current):   # for each pair of filenames
    f1    = CDF(fn_p,NC.NOWRITE)# open last file
    f2    = CDF(fn_c,NC.WRITE)  # open current file

    # Make sure that we are not processing a file which has already been
    # processed by this script
    try:
        test = f2.inq_varid('PRECIP_H') # Attempt to read PRECIP_H
        print ''.join(["File ",fn_c," already processed, skipping"])
        continue    # Move to next iteration (next pair of files)
    except CDFError:
        pass    # If PRECIP_H doesn't exist it is safe to proceed

    # Check that we have 1-hour between files
    t1 = f1.inq_varid('XTIME')
    t2 = f2.inq_varid('XTIME')
    #print t2[:]-t1[:]
    if t1[:].shape != t2[:].shape:
        raise Exception(''.join(["Inconsistent time length of time record in",\
                                 "files: ",fn_p," & ",fn_c,".\n",\
                                 "Both must be of length 1"]) )
    elif t2[:].shape[0] != 1:
        raise Exception(''.join(["Length of time record in ",fn_c," is not 1"]))
    elif t2[:]-t1[:] != 60:
        raise Exception(''.join(["Time between ouput files",
                                 fn_p," & ",fn_c,
                                 "is not 60 min"]))

    # Set the automode flag so that we don't need to worry about setting the
    # define/data mode.
    f2.automode()
    f2.TITLE = ''.join([f2.TITLE,' POST-PROCESSED TO WORK WITH FLX_WRF2'])
    
    # What we aim to do:
    # Check for fields matching our list vnames, any matches 
    # should be subject to our post processing.

    # Predefine hourly precipitation field in current file
    precip_rate = f2.def_var('PRECIP_H', NC.FLOAT,
                             ('Time','south_north','west_east') )
    #print precip_rate[:]
    # Initialize field as 0
    precip_rate[:]=0
    #print precip_rate[:]
    # Set attributes
    precip_rate.FieldType   = 104
    precip_rate.MemoryOrder = 'XY'
    precip_rate.description = 'TOTAL PRECIPIATION SINCE LAST OUTPUT TIME'
    precip_rate.units       = 'mm/[OUTPUT TIME INTERVAL]'
    precip_rate.stagger     = ''
    precip_rate.coordinates = 'XLONG XLAT'

    for v in vnames:
        print(v)
        try:
            try: 
                vin1=f1.inq_varid(v)[:]   # Load variable data
            except CDFError:
                print ''.join(['Warning: Variable "',v,'" missing in "',fn_p,
                               '", skipping'])
                raise
            try:
                vin2=f2.inq_varid(v)[:]   # Load variable data
            except CDFError:
                print ''.join(['Warning: Variable "',v,'" missing in "',fn_c,
                               '", skipping'])
                raise
        except CDFError:
            pass
            continue
        #print(vin1)
        #print(vin2)

        # Add accumulation since last output time to precip_rate
        # In this way, the contribution from each precip-type
        # is added one-by-one
        precip_rate[:] = precip_rate[:]+(vin2[:]-vin1[:])
        #print precip_rate[:]

    # Close the files
    # (probably not required, but good to clarify that we're done)
    del f1,f2
