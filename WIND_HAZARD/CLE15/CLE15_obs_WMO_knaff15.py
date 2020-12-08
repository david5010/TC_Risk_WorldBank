#!/usr/bin/env python
from __future__ import division
from builtins import str
from builtins import range
from past.utils import old_div
import numpy as np
import datetime
import pickle
from netCDF4 import Dataset
import sys
import matplotlib.pyplot as plt
from chaz import CLE15, utility
from pygplib import readbst
import xarray as xr
import pandas as pd

### constant from Dan Chavas ###
fcor = 5.e-5  # [s-1] {5e-5}; Coriolis parameter at storm center
# Environmental parameters
# Outer region
# [-] {1}; 0 : Outer region Cd = constant (defined on next line); 1 : Outer region Cd = f(V) (empirical Donelan et al. 2004)
Cdvary = 1
# [-] {1.5e-3}; ignored if Cdvary = 1; surface momentum exchange (i.e. drag) coefficient
Cd = 1.5e-3
# [ms-1] {2/1000; Chavas et al 2015}; radiative-subsidence rate in the rain-free tropics above the boundary layer top
w_cool = 2./1000

# Inner region
# [-] {1}; 0 : Inner region Ck/Cd = constant (defined on next line); 1 : Inner region Ck/Cd = f(Vmax) (empirical Chavas et al. 2015)
CkCdvary = 1
# [-] {1}; ignored if CkCdvary = 1; ratio of surface exchange coefficients of enthalpy and momentum; capped at 1.9 (things get weird >=2)
CkCd = 1.

# Eye adjustment
eye_adj = 0  # [-] {1}; 0 = use ER11 profile in eye; 1 = empirical adjustment
# [-] {.15; empirical Chavas et al 2015}; V/Vm in eye is reduced by factor (r/rm)^alpha_eye; ignored if eye_adj=0
alpha_eye = .15
###

# for Mumbai
cityName = 'Bermuda'
lat_poi = 32.307
lon_poi = -64.7505+360.
radius = 300.  # km
er = 6371.0  # km

# read data
fileName = '/data2/clee/bttracks/Allstorms.ibtracs_all.v03r10.nc'
ibtracs = readbst.read_ibtracs(fileName, 'atl')
ipoi = utility.find_poi_Tracks(ibtracs.lon[:, :], ibtracs.lat[:, :], ibtracs.wspd[:, :],
                               lon_poi, lat_poi, radius)
lon = ibtracs.lon[:, ipoi]
lat = ibtracs.lat[:, ipoi]
wspd = ibtracs.wspd[:, ipoi]
days = ibtracs.days[:, ipoi]
dist2land = ibtracs.dist2land[:, ipoi]
year = ibtracs.year[ipoi]
tt = np.empty(wspd.shape, dtype=object)
count = 0
for i in range(ipoi.shape[0]):
    for j in range(wspd.shape[0]):
        if days[j, i] == days[j, i]:
            tt[j, count] = datetime.datetime(
                1858, 11, 17, 0, 0)+datetime.timedelta(days=days[j, i])
    count += 1
lon_diff = lon[1:, :]-lon[0:-1, :]
lat_diff = lat[1:, :]-lat[0:-1, :]
londis = old_div(2*np.pi*er*np.cos(old_div(lat[1:, :],180)*np.pi),360)
dx = londis*lon_diff
dy = 110.*lat_diff
days_diff = (days[1:, :] - days[0:-1, :])*24.
tr = old_div(np.sqrt(dx**2+dy**2),(days_diff))
trDir = np.arctan2(lat_diff, lon_diff)
#tr1 = np.zeros(wspd.shape)*np.float('nan')
#trDir1 = np.zeros(wspd.shape)*np.float('nan')
# for iS in range(ipoi.shape[0]):
#    iT = np.argwhere(np.isnan(lon[:,iS])).flatten()[-1]+1
#    trDir1[:iT,iS],tr1[:iT,iS] =\
#        utility.getStormTranslation(lon[:iT,iS],lat[:iT,iS],tt[:iT,iS])
rmax = utility.knaff15(wspd, lat)*1000.  # meter
# tr1 = tr1*3.6 #km/hr

a1, a2, a3, a4, a5, a6, a7, a8, a9 = [[] for _ in range(9)]
for iS in range(lon.shape[1]):
    iipoi = utility.find_timing_Tracks(
        lon[:, iS], lat[:, iS], wspd[:, iS], lon_poi, lat_poi, radius)
    if iipoi.size > 0:
        for niii in np.arange(iipoi.size):
            a1.append(lon[iipoi[niii], iS])
            a2.append(lat[iipoi[niii], iS])
            a3.append(tr[iipoi[niii], iS])
            a4.append(trDir[iipoi[niii], iS])
            a5.append(wspd[iipoi[niii], iS])
            a6.append(iS)
            a7.append(dist2land[iipoi[niii], iS])
            a8.append(np.int(year[iS]))
            a9.append(tt[iipoi[niii], iS])
for iv in range(1, 10):
    exec('a'+str(iv)+'=np.array(a'+str(iv)+')')

ds = xr.Dataset({'lon': (['pt'], a1), 'lat': (['pt'], a2), 'speed': (['pt'], a3),
                 'Dir': (['pt'], a4), 'wspd': (['pt'], a5), 'stormID': (['pt'], a6),
                 'dist2land': (['pt'], a7), 'year': (['pt'], a8), 'date': (['pt'], a9)},
                coords={'pt': list(range(a1.shape[0]))})
ds.to_netcdf('Obs_'+cityName+'_tr_300km.nc', 'w', 'NETCDF3_CLASSIC')

