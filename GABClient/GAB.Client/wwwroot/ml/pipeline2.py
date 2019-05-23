####################################### MALETESS ##################################
################################################################################
# 
#       Copyright (C) 2019 Sebastian L. Hidalgo
#       shidalgo@iac.es
#
#       This program is free software: you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation, version 3 of the License GPLv3.
#   
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#   
#       You should have received a copy of the GNU General Public License
#       along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#       Sebastian L. Hidalgo 
#       Instituto de Astrofisica de Canarias
#       C/ Via Lactea s/n
#       38200 La Laguna
#       S. C. Tenerife
#       SPAIN
#
# 
##################################################################################

import numpy as np
from scipy.fftpack import fft, fftfreq
from scipy import ndimage
from scipy.signal import find_peaks
from sklearn.preprocessing import normalize, StandardScaler
import pickle
import statsmodels.api as stm
import argparse as argp
import sys, json, time
from astropy.io import fits

parser = argp.ArgumentParser(prog='maletess.py',description='This is a Python3 algorithm to make predictions for planets candidates using Machine Learning ', usage='%(prog)s')

parser.add_argument('--version', action='version', version='%(prog)s 1.0')

parser.add_argument('mlf', type=str, help='File trained for ML (pickle file)')

parser.add_argument('lcf', type=str,  help='Light curve file (numpy file .npz) ')

parser.add_argument('tpf', type=str,  help='Target Pixel File (reference file .fits) ')

args = parser.parse_args()

def preplanet(con, onsp, dtime, perd, sigma, FF, LL):

    # files : files to load
    # onsp  : number of frequencies to be sampled
    # dtime : delta_time
    # perd  : Range of periods to be sampled
    
    ########## INTERPOLATE AT A FIXED TIME############
    itime = dtime/(3600*24)
    atime = np.arange(con['time_flat'][0], con['time_flat'][-1], itime)
    flx  = np.interp(atime, con['time_flat'], con['flux_flat'])
    ############################ ###############
    
    flx = np.pad(flx, pad_width = (0, max(0, onsp - len(flx))), mode = 'constant', constant_values = 0) # 0 PADDING      
    flx = flx[:onsp]  # FOR COMPUTATIONAL LIMITS TAKE onsp (must be power of 2 for fft) SAMPLES
    flx = fft(flx)                                        # FFT
    flx = np.abs(flx)[LL]                           # TAKES ONLY FREQUENCIES WITHIN THE RANGE

    ######## GAUSSIAN FILTER ON NOT FLATTEN SIGNAL FOR FINDING PEAKS  #######
    gfl = ndimage.filters.gaussian_filter1d(flx, sigma=1)   
    indk = find_peaks(gfl, distance=1)[0]
    ll = gfl[indk] >= np.mean(gfl) + 1*np.std(gfl)
    if sum(ll) > 0:
        lm = np.argmax(gfl[indk[ll]])    
        per = 1/FF[LL][indk[ll][lm]]/(3600*24)
        per = '{:4.2f}'.format(per)
    else:
        per = '0.00'
    
    ####### FLATTENING THE PROFILE ######
    kk = stm.nonparametric.lowess(flx, FF[LL], frac=0.95)
    flx = flx - kk[:,1]
    flx = ndimage.filters.gaussian_filter1d(flx, sigma=sigma)   # GAUSSIAN FILTER
    
    ####### NORMALIZATION AND STANDARIZATION ######
    flx = normalize(flx.reshape(1,-1))[0]
    flx = scal.fit_transform(flx.reshape(-1,1)).reshape(1,-1)[0]

    
    return flx,  per 

start_time = time.time()

scal = StandardScaler()        

# LARGEST SAMPLE SIZE
sigma = 1
xsp     = int(1024)     # FOR TESS ML-GABLAB
nsp = 2**int(np.floor(np.log2(xsp)))

perd = [0.3*24*3600, 21*24*3600]    # PERIOD RANGE TO BE SAMPLED
dtime = 1800                                     # DELTA TIME FOR INTERPOLATE

#    # CONVERT PERIODS TO FREQUENCIES
frqr = [1/perd[1], 1/perd[0]]
FF = fftfreq(nsp,dtime)
LL = (FF >= frqr[0]) & (FF <= frqr[1])


# LOADING MODEL...
savfil = open(args.mlf, 'rb')
model = pickle.load(savfil)
savfil.close()

# LOADING LIGHT CURVE
con = np.load(args.lcf)

# PREPROCESING LIGHT CURVE
flx, per = preplanet(con, nsp, dtime, perd, sigma, FF, LL) 

# PREDICTION: NO_PLANET,  PLANET
flxprb = model.predict_proba(flx.reshape(1,-1))[0]       

if flxprb[0] > 0.5:
    per = '0.00'

perV = [float(per)]

# RESULTS
hdu = fits.open(args.tpf)
X = hdu[0].header['SECTOR']
TICID = hdu[0].header['TICID']
Camera = hdu[0].header['CAMERA']
CCD = hdu[0].header['CCD']
RA = hdu[0].header['RA_OBJ']
DEC = hdu[0].header['DEC_OBJ']
MAG = hdu[0].header['TESSMAG']
hdu.close()
print('TICID = {}'.format(str(TICID)))
print('Sector = {}'.format(str(X)))
print('Camera = {}'.format(str(Camera)))
print('CCD = {}'.format(str(CCD)))
print('RA = {}'.format(str(RA)))
print('DEC = {}'.format(str(DEC)))
print('Magnitude = {}'.format(str(MAG)))
print("Frequencies = {}".format(perV))
print("Is not a planet = {}".format(flxprb[0]))
print("Is a planet = {}".format(flxprb[1]))

resultfilename = args.lcf.replace("_data.npz", "_data.result")
data = {"ticid": str(TICID), "sector": X, "camera": Camera, "ccd": CCD, "ra": RA, "dec": DEC, "tmag": MAG, "lc": args.lcf, "frequencies": perV, "isnotplanet": flxprb[0], "isplanet": flxprb[1] }
json_data = json.dumps(data)
rf = open(resultfilename, "w")
rf.write(json_data)
rf.close()

print("Total time: {} sec".format(time.strftime("%H:%M:%S", time.gmtime(time.time()-start_time))))