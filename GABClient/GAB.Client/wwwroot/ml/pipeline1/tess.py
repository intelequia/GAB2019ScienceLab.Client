#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .ap import A3d
from .mu import Interpolate, SavGol, Downbin, Scatter
import astropy.io.fits as pyfits
from photutils import SExtractorBackground
import numpy as np
import os, sys, shutil, ast

def Breakpoints(TIC, cadence = 'lc', **kwargs):
    sector = kwargs.get('sector', None)
    if cadence == 'lc':
        breakpoints = {0: [],
                       1: [],
                       2: [],
                       3: [],
                       4: [],
                       5: [],
                       6: [],
                       7: [],
                       8: [],
                       9: [],
                      10: [],
                      11: [],
                      12: [],
                      13: [],
                      14: [],
                      15: [],
                      16: [],
                      17: []}
    else:
        raise ValueError('Invalid value for the cadence.')
    if sector in breakpoints:
        return breakpoints[sector]
    else:
        return None
def CDPP(flux, mask = [], cadence = 'lc'):
    rmswin = 13
    svgwin = 49
    if cadence == 'sc':
        newsize = len(flux) // 30
        flux = Downbin(flux, newsize, operation = 'mean')
    flux_savgol = SavGol(np.delete(flux, mask), win = svgwin)
    if len(flux_savgol):
        return Scatter(flux_savgol / np.nanmedian(flux_savgol), remove_outliers = True, win = rmswin)
    else:
        return np.nan
def GetData(TIC, indir, outdir, cadence = 'lc', S = None, fits = None,
            aperture_name = None, max_pixels = 75, saturation_tolerance = - 0.1,
            bad_bits = [1, 2, 4, 8, 16, 32, 64, 128, 136, 160, 164, 168, 176, 180, 256, 512, 1024, 2048], **kwargs):
    if S is None:
        raise Exception
    sector = ast.literal_eval(S)
    tpf = os.path.join(indir, fits)
    with pyfits.open(tpf) as f:
        qdata = f[1].data
        tpf_aperture = None
        tpf_big_aperture = None,
    apertures = {'tpf': tpf_aperture, 'tpf_big': tpf_big_aperture}
    fitsheader = [pyfits.getheader(tpf, 0).cards,
                  pyfits.getheader(tpf, 1).cards,
                  pyfits.getheader(tpf, 2).cards]
    cadn = np.array(qdata.field('CADENCENO'), dtype = 'int32')
    time = np.array(qdata.field('TIME'), dtype = 'float64')
    fpix = np.array(qdata.field('FLUX'), dtype = 'float64')
    fpix_err = np.array(qdata.field('FLUX_ERR'), dtype = 'float64')
    qual = np.array(qdata.field('QUALITY'), dtype = int)
    naninds = np.where(np.isnan(time))
    time = Interpolate(np.arange(0, len(time)), naninds, time)
    pc1 = np.array(qdata.field('POS_CORR1'), dtype = 'float64')
    pc2 = np.array(qdata.field('POS_CORR2'), dtype = 'float64')
    if not np.all(np.isnan(pc1)) and not np.all(np.isnan(pc2)):
        pc1 = Interpolate(time, np.where(np.isnan(pc1)), pc1)
        pc2 = Interpolate(time, np.where(np.isnan(pc2)), pc2)
    else:
        pc1 = None
        pc2 = None
    f97 = np.zeros((fpix.shape[1], fpix.shape[2]))
    for i in range(fpix.shape[1]):
        for j in range(fpix.shape[2]):
            tmp = np.delete(fpix[:, i, j], np.where(np.isnan(fpix[:, i, j])))
            if len(tmp):
                f = SavGol(tmp)
                med = np.nanmedian(f)
                MAD = 1.4826 * np.nanmedian(np.abs(f - med))
                bad = np.where((f > med + 10. * MAD) | (f < med - 10. * MAD))[0]
                np.delete(tmp, bad)
                i97 = int(0.975 * len(tmp))
                tmp = tmp[np.argsort(tmp)[i97]]
                f97[i, j] = tmp
    sav_ap_name = kwargs.get('sav_aper_name', 'aperture')
    Nmax = np.copy(max_pixels)
    co = 0
    while Nmax >= max_pixels:
        ticmag = fitsheader[0]['TESSMAG'][1]
        if ticmag > 6.5:
            ss = 1.5
        elif 6.5 >= ticmag > 9.:
            ss = 1.3
        elif 9. >= ticmag > 12.:
            ss = 1.2
        elif ticmag < 12.:
            ss = 1.1
        aperture, Nmax = A3d(fpix, N_pixels_max = max_pixels - 1, sigma = ss)
        if np.sum(aperture) == 0.0:
            sys.exit("WARNING: Aperture can't be created, try another TIC")
        elif np.sum(aperture) == 1.0:
            ii = np.where(aperture == 1.)
            try:
                aperture[ii[0] + 1, ii[1]] = 1.
            except:
                pass
            try:
                aperture[ii[0] - 1, ii[1]] = 1.
            except:
                pass
            try:
                aperture[ii[0], ii[1] + 1] = 1.
            except:
                pass
            try:
                aperture[ii[0], ii[1] - 1] = 1.
            except:
                pass
        if fpix.shape[1] < 12 and fpix.shape[2] < 12: break
        if Nmax >= max_pixels:
            nanind = np.where(np.isnan(fpix_err) == 1)
            fpix_err[nanind] = 0.
            bin_row = int(np.ceil(fpix.shape[1] / 12.))
            res_row = fpix.shape[1] % bin_row
            if res_row != 0:
                add_row = bin_row - res_row
                fpix_row = np.ndarray(shape = (fpix.shape[0], fpix.shape[1] + add_row, fpix.shape[2]))
                fpix_err_row = np.ndarray(shape = (fpix.shape[0], fpix.shape[1] + add_row, fpix.shape[2]))
                for fi, fp in enumerate(fpix):
                    SexBkg = SExtractorBackground()
                    fp[fp <= 0.] = 0.0
                    try:
                        fp_bkg = np.ones(fpix.shape[2]) * SexBkg.calc_background(fp)
                    except:
                        fp_bkg = np.zeros(fpix.shape[2])
                    for ad in np.arange(add_row):
                        fp = np.vstack((fp, fp_bkg))
                    fpix_row[fi] = fp
                for fi, fe in enumerate(fpix_err):
                    for ad in np.arange(add_row):
                        fe = np.vstack((fe, np.zeros(fpix_err.shape[2])))
                    fpix_err_row[fi] = fe
                fpix = np.copy(fpix_row)
                fpix_err = np.copy(fpix_err_row)
            bin_col = int(np.ceil(fpix.shape[2] / 12.))
            res_col = fpix.shape[2] % bin_col
            if res_col != 0:
                add_col = bin_col - res_col
                fpix_col = np.ndarray(shape = (fpix.shape[0], fpix.shape[1], fpix.shape[2] + add_col))
                fpix_err_col = np.ndarray(shape = (fpix.shape[0], fpix.shape[1], fpix.shape[2] + add_col))
                for fi, fp in enumerate(fpix):
                    SexBkg = SExtractorBackground()
                    fp[fp <= 0.] = 0.0
                    try:
                        fp_bkg = np.ones(fpix.shape[1]) * SexBkg.calc_background(fp)
                    except:
                        fp_bkg = np.zeros(fpix.shape[1])
                    fp_bkg = fp_bkg.reshape(fp_bkg.shape[0], 1)
                    for ad in np.arange(add_col):
                        fp = np.hstack((fp, fp_bkg))
                    fpix_col[fi] = fp
                for fi, fe in enumerate(fpix_err):
                    for ad in np.arange(add_col):
                        fe = np.hstack((fe, np.zeros(shape = (fpix.shape[1], 1))))
                fpix = np.copy(fpix_col)
                fpix_err = np.copy(fpix_err_col)
            fpix_bin = np.ndarray(shape = (fpix.shape[0], fpix[i].shape[0] // bin_row, fpix[i].shape[1] // bin_col))
            for i, f in enumerate(fpix_bin):
                fpix_bin[i] = fpix[i].reshape(fpix[i].shape[0] // bin_row, bin_row,
                                              fpix[i].shape[1] // bin_col, bin_col).sum(3).sum(1)
            fpix = np.copy(fpix_bin)
            fpix_err_bin = np.ndarray(shape = (fpix_err.shape[0],
                                               fpix_err[0].shape[0] // bin_row,
                                               fpix_err[0].shape[1] // bin_col))
            for i, f in enumerate(fpix_err_bin):
                fpix_err_bin[i] = fpix_err[i].reshape(fpix_err[i].shape[0] // bin_row, bin_row,
                                                      fpix_err[i].shape[1] // bin_col, bin_col).sum(3).sum(1)
            fpix_err = np.copy(fpix_err_bin)
        co += 1
    apertures.update({'automatic': aperture})
    pixel_images = [fpix[0], fpix[len(fpix) // 2], fpix[len(fpix) - 1]]
    if np.sum(aperture) > max_pixels:
        keys = list(apertures.keys())
        npix = np.array([np.sum(apertures[k]) for k in keys])
        aperture_name = keys[np.argmax(npix * (npix <= max_pixels))]
        aperture = apertures[aperture_name]
        aperture[np.isnan(fpix[0])] = 0
        if np.sum(aperture) > max_pixels:
            raise Exception('No apertures available with fewer than {} pixels. Aborting...'.format(max_pixels))
    aperture[np.isnan(fpix[0])] = 0
    ap = np.where(aperture == 1)
    fpix2D = np.array([f[ap] for f in fpix], dtype = 'float64')
    fpix_err2D = np.array([p[ap] for p in fpix_err], dtype = 'float64')
    binds = np.where(aperture != 1)
    if len(binds[0]) > 0 and sector not in [9, 10, 11]:
        bkg = np.nanmedian(np.array([f[binds] for f in fpix], dtype = 'float64'), axis = 1)
        bkg_err = 1.253 * np.nanmedian(np.array([e[binds] for e in fpix_err],
                          dtype='float64'), axis = 1) / np.sqrt(len(binds[0]))
        bkg = bkg.reshape(-1, 1)
        bkg_err = bkg_err.reshape(-1, 1)
    elif len(binds[0]) > 0 and sector in [9, 10, 11]:
        bkg = np.zeros_like(fpix2D)
        bkg_err = np.zeros_like(fpix2D)
    else:
        bkg = np.zeros_like(fpix2D)
        bkg_err = np.zeros_like(fpix2D)
    fpix = fpix2D - bkg
    fpix_err = np.sqrt(fpix_err2D ** 2 + bkg_err ** 2)
    flux = np.sum(fpix, axis = 1)
    ferr = np.sqrt(np.sum(fpix_err ** 2, axis = 1))
    nanmask = np.where(np.isnan(flux) | (flux == 0))[0]
    badmask = []
    for b in bad_bits:
        badmask += list(np.where(qual == b)[0])
    tmpmask = np.array(list(set(np.concatenate([badmask, nanmask]))))
    t = np.delete(time, tmpmask)
    f = np.delete(flux, tmpmask)
    f = SavGol(f)
    med = np.nanmedian(f)
    MAD = 1.4826 * np.nanmedian(np.abs(f - med))
    bad = np.where((f > med + 10. * MAD) | (f < med - 10. * MAD))[0]
    outmask = [np.argmax(time == t[i]) for i in bad]
    fpix = Interpolate(time, nanmask, fpix)
    fpix_err = Interpolate(time, nanmask, fpix_err)
    data = dict(ID = TIC, sector = sector, cadn = cadn, time = time, fpix = fpix,
                fpix_err = fpix_err, nanmask = np.sort(nanmask), badmask = np.sort(badmask),
                outmask = np.sort(outmask), aperture = aperture,
                apertures = apertures, pixel_images = pixel_images, bkg = bkg,
                qual = qual, pc1 = pc1, pc2 = pc2, fitsheader = fitsheader,
                tessmag = fitsheader[0]['TESSMAG'][1], radius = fitsheader[0]['RADIUS'][1],
                ra = fitsheader[0]['RA_OBJ'][1], dec = fitsheader[0]['DEC_OBJ'][1],
                pmra = fitsheader[0]['PMRA'][1], pmdec = fitsheader[0]['PMDEC'][1],
                teff = fitsheader[0]['TEFF'][1], pmtotal = fitsheader[0]['PMTOTAL'][1],
                logg = fitsheader[0]['LOGG'][1], feh = fitsheader[0]['MH'][1])
    return data
