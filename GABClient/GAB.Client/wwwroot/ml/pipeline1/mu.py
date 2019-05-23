#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from scipy.signal import savgol_filter
import sys

def Interpolate(time, mask, y):
    yy = np.array(y)
    t_ = np.delete(time, mask)
    y_ = np.delete(y, mask, axis = 0)
    if len(yy.shape) == 1:
        yy[mask] = np.interp(time[mask], t_, y_)
    elif len(yy.shape) == 2:
        for n in range(yy.shape[1]):
            yy[mask, n] = np.interp(time[mask], t_, y_[:, n])
    else:
        raise Exception("Array ``y`` must be either 1- or 2-d.")
    return yy

def Chunks(l, n, all = False):
    if all:
        jarr = range(0, n - 1)
    else:
        jarr = [0]

    for j in jarr:
        for i in range(j, len(l), n):
            if i + 2 * n <= len(l):
                yield l[i:i + n]
            else:
                if not all:
                    yield l[i:]
                break

def Smooth(x, window_len = 100, window = 'hanning'):
    if window_len == 0:
        return np.zeros_like(x)
    s = np.r_[2 * x[0] - x[window_len - 1::-1], x, 2 * x[-1] - x[-1:-window_len:-1]]
    if window == 'flat':
        w = np.ones(window_len, 'd')
    else:
        w = eval('np.' + window + '(window_len)')
    y = np.convolve(w / w.sum(), s, mode = 'same')
    return y[window_len:-window_len + 1]

def Scatter(y, win = 13, remove_outliers = False):
    if remove_outliers:
        if len(y) >= 50:
            ys = y - Smooth(y, 50)
        else:
            ys = y
        M = np.nanmedian(ys)
        MAD = 1.4826 * np.nanmedian(np.abs(ys - M))
        out = []
        for i, _ in enumerate(y):
            if (ys[i] > M + 5 * MAD) or (ys[i] < M - 5 * MAD):
                out.append(i)
        out = np.array(out, dtype = int)
        y = np.delete(y, out)
    if len(y):
        return 1.e6 * np.nanmedian([np.std(yi) / np.sqrt(win) for yi in Chunks(y, win, all = True)])
    else:
        return np.nan

def SavGol(y, win = 49):
    if len(y) >= win:
        return y - savgol_filter(y, win, 2) + np.nanmedian(y)
    else:
        return y

def _float(s):
    try:
        res = float(s)
    except:
        res = np.nan
    return res

def Downbin(x, newsize, axis = 0, operation = 'mean'):
    assert newsize < x.shape[axis], "The new size of the array must be smaller than the current size."
    oldsize = x.shape[axis]
    newshape = list(x.shape)
    newshape[axis] = newsize
    newshape.insert(axis + 1, oldsize // newsize)
    trim = oldsize % newsize
    if trim:
        xtrim = x[:-trim]
    else:
        xtrim = x

    if operation == 'mean':
        xbin = np.nanmean(xtrim.reshape(newshape), axis = axis + 1)
    elif operation == 'sum':
        xbin = np.nansum(xtrim.reshape(newshape), axis = axis + 1)
    elif operation == 'quadsum':
        xbin = np.sqrt(np.nansum(xtrim.reshape(newshape) ** 2, axis = axis + 1))
    elif operation == 'median':
        xbin = np.nanmedian(xtrim.reshape(newshape), axis = axis + 1)
    else:
        raise ValueError("`operation` must be either `mean`, `sum`, `quadsum`, or `median`.")

    return xbin
