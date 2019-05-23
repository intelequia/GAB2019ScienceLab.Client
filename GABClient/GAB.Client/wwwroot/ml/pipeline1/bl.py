#!/usr/bin/env python
# -*- coding: utf-8 -*-
from statsmodels.nonparametric.smoothers_lowess import lowess
from astropy.stats import sigma_clipped_stats
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter
import matplotlib.pyplot as plt
import numpy as np
import os, sys, shutil, re, ast, warnings
warnings.filterwarnings(action = "ignore", module = "numpy", message = "^Mean of empty slice")

def eebls(intime, indata, inerr, minper, maxper, mindur, maxdur, nsearch, nbins):
    np.seterr(all='ignore')
    status = 0
    if status == 0:
        tr = intime[-1] - intime[0]
        if maxper > tr:
            status = 1
    if status == 0:
        work1 = intime - intime[0]
        work2 = indata - np.mean(indata)
    if status == 0:
        srMax = np.array([], dtype='float32')
        transitDuration = np.array([], dtype='float32')
        transitPhase = np.array([], dtype='float32')
        ingrees = np.array([], dtype='float32')
        egrees = np.array([], dtype='float32')
        dPeriod = (maxper - minper) / nsearch
        trialPeriods = np.linspace(minper**-1, maxper**-1, num = nsearch, dtype = 'float32')**-1
        for trialPeriod in trialPeriods:
            srMax = np.append(srMax, 0.0)
            transitDuration = np.append(transitDuration, np.nan)
            transitPhase = np.append(transitPhase, np.nan)
            ingrees = np.append(ingrees, np.nan)
            egrees = np.append(egrees, np.nan)
            trialFrequency = 1.0 / trialPeriod
            duration1 = max(int(float(nbins) * mindur / 24.0 / trialPeriod), 2)
            duration2 = max(int(float(nbins) * maxdur / 24.0 / trialPeriod) + 1, duration1 + 1)
            halfHour = int(0.02083333 / trialPeriod * nbins + 1)
            work4 = np.zeros((nbins), dtype='float32')
            work5 = np.zeros((nbins), dtype='float32')
            phase = np.array(((work1 * trialFrequency) - np.floor(work1 * trialFrequency)) * float(nbins), dtype='int')
            ptuple = np.array([phase, work2, inerr])
            ptuple = np.rot90(ptuple, 3)
            phsort = np.array(sorted(ptuple, key=lambda ph: ph[2]))
            for i in range(nbins):
                elements = np.nonzero(phsort[:, 2] == float(i))[0]
                work4[i] = np.mean(phsort[elements, 1])
                work5[i] = np.sqrt(np.sum(np.power(phsort[elements, 0], 2)) / len(elements))
            work4 = np.append(work4, work4[:duration2])
            work5 = np.append(work5, work5[:duration2])
            sigmaSum = np.nansum(np.power(work5, -2))
            omega = np.power(work5, -2) / sigmaSum
            s = omega * work4
            for i1 in range(nbins):
                for duration in range(duration1, duration2 + 1, int(halfHour)):
                    i2 = i1 + duration
                    sr1 = np.sum(np.power(s[i1:i2], 2))
                    sr2 = np.sum(omega[i1:i2])
                    sr = np.sqrt(sr1 / (sr2 * (1.0 - sr2)))
                    if sr > srMax[-1]:
                        srMax[-1] = sr
                        transitDuration[-1] = float(duration)
                        transitPhase[-1] = float((i1 + i2) / 2)
                        ingrees[-1] = i1
                        egrees[-1] = i2
        bestSr = np.max(srMax)
        bestTrial = np.nonzero(srMax == bestSr)[0][0]
        srMax /= bestSr
        t0 = np.array(transitPhase * trialPeriods / nbins, dtype = 'float64') + intime[0]
        ingrees = np.array(ingrees * trialPeriods / nbins, dtype = 'float64') + intime[0]
        egrees = np.array(egrees * trialPeriods / nbins, dtype = 'float64') + intime[0]
        transitDuration = egrees - ingrees
    if status == 0:
        ptime = np.copy(trialPeriods)
        pout = np.copy(srMax)
        ptime = np.insert(ptime, [0], [ptime[0]])
        ptime = np.append(ptime, [ptime[-1]])
        pout = np.insert(pout, [0], [0.0])
        pout = np.append(pout, 0.0)
    return srMax, trialPeriods, transitDuration, t0, ingrees, egrees

def eebls2(intime, indata, inerr, minper, maxper, mindur, maxdur, nsearch, nbins):
    np.seterr(all='ignore')
    status = 0
    if status == 0:
        tr = intime[-1] - intime[0]
        if maxper > tr:
            status = 1
    if status == 0:
        work1 = intime - intime[0]
        work2 = indata - np.mean(indata)
    if status == 0:
        srMax = np.array([], dtype='float32')
        transitDuration = np.array([], dtype='float32')
        transitPhase = np.array([], dtype='float32')
        ingrees = np.array([], dtype='float32')
        egrees = np.array([], dtype='float32')
        dPeriod = (maxper - minper) / nsearch
        trialPeriods = np.arange(minper, maxper + dPeriod, dPeriod, dtype='float32')
        for trialPeriod in trialPeriods:
            srMax = np.append(srMax, 0.0)
            transitDuration = np.append(transitDuration, np.nan)
            transitPhase = np.append(transitPhase, np.nan)
            ingrees = np.append(ingrees, np.nan)
            egrees = np.append(egrees, np.nan)
            trialFrequency = 1.0 / trialPeriod
            duration1 = max(int(float(nbins) * mindur / 24.0 / trialPeriod), 2)
            duration2 = max(int(float(nbins) * maxdur / 24.0 / trialPeriod) + 1, duration1 + 1)
            halfHour = int(0.02083333 / trialPeriod * nbins + 1)
            work4 = np.zeros((nbins), dtype='float32')
            work5 = np.zeros((nbins), dtype='float32')
            phase = np.array(((work1 * trialFrequency) - np.floor(work1 * trialFrequency)) * float(nbins), dtype='int')
            ptuple = np.array([phase, work2, inerr])
            ptuple = np.rot90(ptuple, 3)
            phsort = np.array(sorted(ptuple, key=lambda ph: ph[2]))
            for i in range(nbins):
                elements = np.nonzero(phsort[:, 2] == float(i))[0]
                work4[i] = np.mean(phsort[elements, 1])
                work5[i] = np.sqrt(np.sum(np.power(phsort[elements, 0], 2)) / len(elements))
            work4 = np.append(work4, work4[:duration2])
            work5 = np.append(work5, work5[:duration2])
            sigmaSum = np.nansum(np.power(work5, -2))
            omega = np.power(work5, -2) / sigmaSum
            s = omega * work4
            for i1 in range(nbins):
                for duration in range(duration1, duration2 + 1, int(halfHour)):
                    i2 = i1 + duration
                    sr1 = np.sum(np.power(s[i1:i2], 2))
                    sr2 = np.sum(omega[i1:i2])
                    sr = np.sqrt(sr1 / (sr2 * (1.0 - sr2)))
                    if sr > srMax[-1]:
                        srMax[-1] = sr
                        transitDuration[-1] = float(duration)
                        transitPhase[-1] = float((i1 + i2) / 2)
                        ingrees[-1] = i1
                        egrees[-1] = i2
        bestSr = np.max(srMax)
        bestTrial = np.nonzero(srMax == bestSr)[0][0]
        srMax /= bestSr
        t0 = np.array(transitPhase * trialPeriods / nbins, dtype = 'float64') + intime[0]
        ingrees = np.array(ingrees * trialPeriods / nbins, dtype = 'float64') + intime[0]
        egrees = np.array(egrees * trialPeriods / nbins, dtype = 'float64') + intime[0]
        transitDuration = egrees - ingrees
    if status == 0:
        ptime = np.copy(trialPeriods)
        pout = np.copy(srMax)
        ptime = np.insert(ptime, [0], [ptime[0]])
        ptime = np.append(ptime, [ptime[-1]])
        pout = np.insert(pout, [0], [0.0])
        pout = np.append(pout, 0.0)
    return srMax, trialPeriods, transitDuration, t0, ingrees, egrees

def bl(time, flux, ferr, outdir, **kwargs):
    nf = 6000
    nf2 = 6000
    qmin = 0.005
    qmax = 0.1
    threshold0 = 6.0
    threshold1 = 6.0
    per_min = 1.0
    per_max = 5.1
    per_min2 = 4.9
    per_max2 = 75.0

    lon = round((time[-1] - time[0]) / per_max, 1)
    nbin = len(time[time <= per_min + time[0]])
    nt = len(time)
    maxper = (time[nt - 1] - time[0]) / lon
    minper = time[nbin] - time[0]
    frec = np.linspace(maxper**-1, minper**-1, num = nf)
    poT, ptime, duration, t0, ingrees, egrees = eebls(time, flux, ferr,
                       maxper, minper, qmin, qmax, nf, nbin)
    ind_nan = np.where(np.isnan(poT) == True)[0]
    poT = np.delete(poT, ind_nan)
    ptime = np.delete(ptime, ind_nan)
    ftimeT = ptime**-1
    poT /= np.nanmedian(poT)
    filter2 = lowess(poT, ftimeT, is_sorted = True, frac = 0.3, it = 0)
    poT /= filter2[:, 1]
    ftimeT = filter2[:, 0]
    a = np.array([ftimeT, poT])
    a = a.transpose()
    a = a[a[:, 0].argsort()]
    a = a.transpose()
    ftimeT = a[0]
    poT = a[1]
    filter2 = lowess(poT, ftimeT, is_sorted = False, frac = 0.3, it = 0)
    poT2 = filter2[:, 1]
    desviacion = poT - poT2
    des_std = np.std(desviacion)
    conf = poT2 + threshold0 * des_std
    periodos = ftimeT[np.where(poT > conf[::-1])[0]]**-1
    t0s = t0[np.where(poT > conf[::-1])[0]]
    ing = ingrees[np.where(poT > conf[::-1])[0]]
    egr = egrees[np.where(poT > conf[::-1])[0]]
    dur = duration[np.where(poT > conf[::-1])[0]]
    lon = round((time[-1] - time[0]) / per_max2, 1)
    nbin = len(time[time <= per_min2 + time[0]])
    nt = len(time)
    maxper = (time[nt - 1] - time[0]) / lon
    minper = time[nbin] - time[0]
    frec2 = np.linspace(maxper**-1, minper**-1, num = nf2)
    poT3, ptime3, duration3, t03, ingrees3, egrees3 = eebls2(time, flux, ferr,
                       maxper, minper, qmin, qmax, nf2, nbin)
    ftimeT3 = ptime3**-1
    poT3 /= np.nanmedian(poT3)
    filter2 = lowess(poT3, ftimeT3, is_sorted = True, frac = 0.3, it = 0)
    poT3 /= filter2[:, 1]
    ftimeT3 = filter2[:, 0]
    a = np.array([ftimeT3, poT3])
    a = a.transpose()
    a = a[a[:, 0].argsort()]
    a = a.transpose()
    ftimeT3 = a[0]
    poT3 = a[1]
    filter3 = lowess(poT3, ftimeT3, is_sorted = False, frac = 0.3, it = 0)
    poT4 = filter3[:, 1]
    desviacion = poT3 - poT4
    des_std2 = np.std(desviacion)
    conf2 = poT4 + threshold1 * des_std2
    periodos2 = ftimeT3[np.where(poT3 > conf2[::-1])[0]]**-1
    t0s2 = t03[np.where(poT3 > conf2[::-1])[0]]
    ing2 = ingrees3[np.where(poT3 > conf2[::-1])[0]]
    egr2 = egrees3[np.where(poT3 > conf2[::-1])[0]]
    dur2 = duration3[np.where(poT3 > conf2[::-1])[0]]
    periodos3 = np.concatenate((periodos, periodos2))
    t0s3 = np.concatenate((t0s, t0s2))
    return len(periodos3), np.unique(periodos3.astype(int))
