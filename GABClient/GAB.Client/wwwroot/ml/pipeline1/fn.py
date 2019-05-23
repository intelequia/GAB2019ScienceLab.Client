#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .mu import SavGol, Scatter
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy.interpolate import interp1d
import numpy as np
import os, sys, ast, re
import warnings

warnings.filterwarnings(action = "ignore", module = "scipy", message = "^internal gelsd")

def Sf(time, flux, ferr, **kwargs):
    sortedd = kwargs.get('sort_data', True)
    frac = kwargs.get('fraction_rate', 0.03)
    it = kwargs.get('iterations', 3)
    rmswin = kwargs.get('points_window', 13)
    svgwin = int(rmswin * 3)
    flux_orig = np.copy(flux)
    flux_orig2 = np.copy(flux)
    flux_savgol = SavGol(flux, win = svgwin)
    sigma2 = Scatter(flux_savgol / np.nanmedian(flux_savgol), remove_outliers = True, win = rmswin)
    sigma = np.ones(40) * 3.
    for i in range(len(sigma)):
        if i > 0:
            not_nan = np.logical_not(np.isnan(flux_orig2))
            indices = np.arange(len(flux_orig2))
            interp = interp1d(indices[not_nan], flux_orig2[not_nan],
                              kind = 'nearest',
                              bounds_error = False,
                              fill_value = 'extrapolate')
            flux_orig2 = interp(indices)

        filtered = lowess(flux_orig2, time, is_sorted = sortedd, frac = frac, it = it)

        time_filter = filtered[:, 0]
        flux_filter = filtered[:, 1]

        std = np.std(flux_orig2 - flux_filter)
        if std < sigma2:
            break

        index = np.where(abs(flux_orig2 - flux_filter) > sigma[i] * std)[0]
        np.put(flux_orig2, index, np.nan)

    return flux_orig / flux_filter, ferr / flux_filter
