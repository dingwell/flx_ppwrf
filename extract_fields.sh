#!/bin/bash
# Extract fields for use in WRF and store in archive
# Usage:
#   extract_fields file1 [file2[,...]] output-directory

# Set deflation level:
export DFL_LVL=1   # 0=no compression, 9=max; higher than is rather pointless
# Variables used by WRF
VAR2D=ZNU,ZNW
VAR3D=XLAT,XLONG,MAPFAC_M,PSFC,U10,V10,T2,Q2,SWDOWN,RAINNC,RAINC,HFX,UST
VAR4D=PB,P,PBLH,PHB,PHB,T,QVAPOR,TKE_PBL # also works with "TKE"
VAR4D_WIND=U,V,W,WW
# Additional variables (for further analysis or compatibility)
VAR_EXTRAS=SR
export VARS="$VAR2D,$VAR3D,$VAR4D,$VAR4D_WIND,$VAR_EXTRAS"

# Precipitation fields
# These fields are not normally read by FLX-WRF but have to be included
# if cloud physics schemes output to them, otherwise precipitation will
# be under estimated.
PRECIP_C=RAINSH
PRECIP_NC=SNOWNC,GRAUPELNC,HAILNC
# WARNING: SNOWC is snow _cover_ (not "accumulated convective snow precip")

# Read input arguments:
NARGIN=$#
let NFILES=NARGIN-1
FILES=${@:1:$NFILES}
OUTDIR=${!#}

# Functions:
copy_vars(){
    local INFILE=$1
    local OUTFILE=$2
    ncks -O --fl_fmt=netcdf4 -L"$DFL_LVL" -v"$VARS" "$INFILE" "$OUTFILE"
}

#MAIN#
COUNT=0
for i in $FILES; do
    let COUNT=COUNT+1
    echo -e "FILE $COUNT:\t$i"
    copy_vars $i "$OUTDIR/$i"
done
