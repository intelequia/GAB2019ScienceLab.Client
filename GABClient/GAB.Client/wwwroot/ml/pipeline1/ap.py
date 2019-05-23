#!/usr/bin/env python
# -*- coding: utf-8 -*-

from photutils import find_peaks, SigmaClip, Background2D, MedianBackground
from copy import copy
from itertools import count
import matplotlib.pyplot as plt
import numpy as np
import sys, os, warnings

warnings.filterwarnings(action = "ignore", module = "photutils", message = "^invalid value encountered")

def A3d(data, **kwargs):
    which = kwargs.get('chosen_by', 'prox')
    data_sum = np.nansum(data, axis = 0)
    Npixels = kwargs.get('N_pixels_max', data_sum.shape[0] * data_sum.shape[1] / 2.)
    sigma = kwargs.get('sigma', 2.)
    data_sum_noneg = np.copy(data_sum)
    data_sum_noneg[data_sum_noneg <= 0.] = 0.0
    bkg2D = Background2D(data_sum_noneg, data_sum_noneg.shape, filter_size = (2, 2),
                         sigma_clip = SigmaClip(sigma = 3., iters = 2),
                         bkg_estimator = MedianBackground())
    bkg = np.unique(bkg2D.background)
    tbl = find_peaks(data_sum, threshold = bkg)
    x0 = int(data[int(data.shape[0] * 2 / 3)].shape[1] / 2.)
    y0 = int(data[int(data.shape[0] * 2 / 3)].shape[0] / 2.)
    dist = np.array([])
    for i in range(len(tbl['x_peak'])):
        dist = np.append(dist, np.sqrt((x0 - tbl['x_peak'][i])**2 + (y0 - tbl['y_peak'][i])**2))
    if which == 'prox':
        chosen = np.where(dist == min(dist))[0]
        if len(chosen) > 1:
            for i in chosen:
                vec_chos = np.array([tbl['peak_value'][i], tbl['peak_value'][i]])
            chosen = np.where(tbl['peak_value'] == max(vec_chos))[0]
    elif which == 'mxpeak':
        chosen = np.where(tbl['peak_value'] == max(tbl['peak_value']))[0]
    cx = int(tbl['x_peak'][chosen])
    cy = int(tbl['y_peak'][chosen])
    aperture = np.zeros_like(data_sum)
    aperture[cy, cx] = 1.
    c = 1
    x = cy
    y = cx
    for n in count(start = 1, step = 1):
        if n > data_sum.shape[0] and n > data_sum.shape[1]: break
        if n % 2:
            x += 1
            try:
                if data_sum[x, y] >= sigma * bkg:
                    try:
                        A0 = aperture[x + 1, y] == 1
                    except:
                        A0 = False
                    try:
                        A1 = aperture[x - 1, y] == 1
                    except:
                        A1 = False
                    try:
                        A2 = aperture[x, y + 1] == 1
                    except:
                        A2 = False
                    try:
                        A3 = aperture[x, y - 1] == 1
                    except:
                        A3 = False
                    if A0 or A1 or A2 or A3:
                        aperture[x, y] = 1
                        c += 1
                        if c >= Npixels: break
            except:
                pass
            for i in range(n):
                y -= 1
                try:
                    if data_sum[x, y] >= sigma * bkg:
                        try:
                            B0 = aperture[x + 1, y] == 1
                        except:
                            B0 = False
                        try:
                            B1 = aperture[x - 1, y] == 1
                        except:
                            B1 = False
                        try:
                            B2 = aperture[x, y + 1] == 1
                        except:
                            B2 = False
                        try:
                            B3 = aperture[x, y - 1] == 1
                        except:
                            B3 = False
                        if B0 or B1 or B2 or B3:
                            aperture[x, y] = 1
                            c += 1
                            if c >= Npixels: break
                except:
                    pass
            for i in range(n):
                x -= 1
                try:
                    if data_sum[x, y] >= sigma * bkg:
                        try:
                            C0 = aperture[x + 1, y] == 1
                        except:
                            C0 = False
                        try:
                            C1 = aperture[x - 1, y] == 1
                        except:
                            C1 = False
                        try:
                            C2 = aperture[x, y + 1] == 1
                        except:
                            C2 = False
                        try:
                            C3 = aperture[x, y - 1] == 1
                        except:
                            C3 = False
                        if C0 or C1 or C2 or C3:
                            aperture[x, y] = 1
                            c +=1
                            if c >= Npixels: break
                except:
                    pass
        else:
            x -= 1
            try:
                if data_sum[x, y] >= sigma * bkg:
                    try:
                        D0 = aperture[x + 1, y] == 1
                    except:
                        D0 = False
                    try:
                        D1 = aperture[x - 1, y] == 1
                    except:
                        D1 = False
                    try:
                        D2 = aperture[x, y + 1] == 1
                    except:
                        D2 = False
                    try:
                        D3 = aperture[x, y - 1] == 1
                    except:
                        D3 = False
                    if D0 or D1 or D2 or D3:
                        aperture[x, y] = 1
                        c += 1
                        if c >= Npixels: break
            except:
                pass
            for i in range(n):
                y += 1
                try:
                    if data_sum[x, y] >= sigma * bkg:
                        try:
                            E0 = aperture[x + 1, y] == 1
                        except:
                            E0 = False
                        try:
                            E1 = aperture[x - 1, y] == 1
                        except:
                            E1 = False
                        try:
                            E2 = aperture[x, y + 1] == 1
                        except:
                            E2 = False
                        try:
                            E3 = aperture[x, y - 1] == 1
                        except:
                            E3 = False
                        if E0 or E1 or E2 or E3:
                            aperture[x, y] = 1
                            c += 1
                            if c >= Npixels: break
                except:
                    pass
            for i in range(n):
                x += 1
                try:
                    if data_sum[x, y] >= sigma * bkg:
                        try:
                            F0 = aperture[x + 1, y] == 1
                        except:
                            F0 = False
                        try:
                            F1 = aperture[x - 1, y] == 1
                        except:
                            F1 = False
                        try:
                            F2 = aperture[x, y + 1] == 1
                        except:
                            F2 = False
                        try:
                            F3 = aperture[x, y - 1] == 1
                        except:
                            F3 = False
                        if F0 or F1 or F2 or F3:
                            aperture[x, y] = 1
                            c +=1
                            if c >= Npixels: break
                except:
                    pass
    if which == 'prox':
        no_chosen = np.where(dist != min(dist))[0]
    elif which == 'mxpeak':
        no_chosen = np.where(tbl['peak_value'] != max(tbl['peak_value']))[0]

    for k in no_chosen:
        ncy = int(tbl['x_peak'][k])
        ncx = int(tbl['y_peak'][k])

        aperture[ncx, ncy] = 0
        try:
            aperture[ncx + 1, ncy] = 0
        except:
            pass
        try:
            aperture[ncx, ncy + 1] = 0
        except:
            pass
        try:
            aperture[ncx - 1, ncy] = 0
        except:
            pass
        try:
            aperture[ncx, ncy - 1] = 0
        except:
            pass
        try:
            aperture[ncx + 1, ncy + 1] = 0
        except:
            pass
        try:
            aperture[ncx + 1, ncy - 1] = 0
        except:
            pass
        try:
            aperture[ncx - 1, ncy - 1] = 0
        except:
            pass
        try:
            aperture[ncx - 1, ncy - 1] = 0
        except:
            pass
        try:
            aperture[ncx - 1, ncy + 1] = 0
        except:
            pass
        try:
            aperture[ncx - 1, ncy - 1] = 0
        except:
            pass

    return aperture, c
