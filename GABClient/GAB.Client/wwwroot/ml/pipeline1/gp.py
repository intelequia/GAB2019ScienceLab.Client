#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, print_function, absolute_import, unicode_literals

from .mu import Chunks
from scipy.optimize import fmin_l_bfgs_b
from scipy.signal import savgol_filter
import numpy as np
np.random.seed(48151623)
import george
from george.kernels import WhiteKernel, Matern32Kernel, ExpSine2Kernel
import sys, os


def GP(kernel, kernel_params, white = False):
    if kernel == 'Basic':
        w, a, t = kernel_params
        if white:
            return george.GP(WhiteKernel(w ** 2) + a ** 2 * Matern32Kernel(t ** 2))
        else:
            return george.GP(a ** 2 * Matern32Kernel(t ** 2))
    elif kernel == 'QuasiPeriodic':
        w, a, g, p = kernel_params
        if white:
            return george.GP(WhiteKernel(w ** 2) + a ** 2 * ExpSine2Kernel(g, p))
        else:
            return george.GP(a ** 2 * ExpSine2Kernel(g, p))
    else:
        raise ValueError('Invalid value for `kernel`.')
def GetCovariance(kernel, kernel_params, time, errors):
    K = np.diag(errors**2)
    K += GP(kernel, kernel_params, white = False).get_matrix(time)
    return K
def GetKernelParams(time, flux, errors, kernel = 'Basic', mask = [], giter = 3, gmaxf = 200, guess = None):
    time = np.delete(time, mask)
    flux = np.delete(flux, mask)
    errors = np.delete(errors, mask)
    f = flux - savgol_filter(flux, 49, 2) + np.nanmedian(flux)
    med = np.nanmedian(f)
    MAD = 1.4826 * np.nanmedian(np.abs(f - med))
    mask = np.where((f > med + 5 * MAD) | (f < med - 5 * MAD))[0]
    time = np.delete(time, mask)
    flux = np.delete(flux, mask)
    errors = np.delete(errors, mask)
    white = np.nanmedian([np.nanstd(c) for c in Chunks(flux, 13)])
    amp = np.nanstd(flux)
    tau = 30.0
    if kernel == 'Basic':
        if guess is None:
            guess = [white, amp, tau]
        bounds = [[0.1 * white, 10. * white],
                  [1., 10000. * amp],
                  [0.5, 100.]]
    elif kernel == 'QuasiPeriodic':
        if guess is None:
            guess = [white, amp, tau, 1., 20.]
        bounds = [[0.1 * white, 10. * white],
                  [1., 10000. * amp],
                  [1e-5, 1e2],
                  [0.02, 100.]]
    else:
        raise ValueError('Invalid value for "kernel"')
    llbest = -np.inf
    xbest = np.array(guess)
    for i in range(giter):
        iguess = [np.inf for g in guess]
        for j, b in enumerate(bounds):
            tries = 0
            while (iguess[j] < b[0]) or (iguess[j] > b[1]):
                iguess[j] = (1 + 0.5 * np.random.randn()) * guess[j]
                tries += 1
                if tries > 100:
                    iguess[j] = b[0] + np.random.random() * (b[1] - b[0])
                    break
        x = fmin_l_bfgs_b(NegLnLike, iguess, approx_grad = False,
                          bounds = bounds, args = (time, flux, errors, kernel),
                          maxfun = gmaxf)
        if -x[1] > llbest:
            llbest = -x[1]
            xbest = np.array(x[0])

    return xbest

def NegLnLike(x, time, flux, errors, kernel):
    gp = GP(kernel, x, white = True)
    gp.compute(time, errors)
    nll = -gp.lnlikelihood(flux)
    ngr = -gp.grad_lnlikelihood(flux) / gp.kernel.pars
    return nll, ngr
