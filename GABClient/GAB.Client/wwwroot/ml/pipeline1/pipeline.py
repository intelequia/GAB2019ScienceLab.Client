#!/usr/bin/env python
# -*- coding: utf-8 -*-
import matplotlib.pyplot as plt
from .gp import GetCovariance, GetKernelParams, GP
from .bs import Basecamp
from .tess import Breakpoints, GetData
from .mu import Chunks, SavGol
from .fn import Sf
from .bl import bl
import numpy as np
import os, re, time, sys, shutil, ast

def tess_pipeline(tess_file, indir, outdir, **kwargs):
    #if not os.path.exists(os.path.join(outdir, '{}_data.npz'.format(re.findall('[0-9]+', tess_file)[3]))) or 1:
    TESS = pipeline(tess_file, indir, outdir, cadence = kwargs.get('cadence', 'lc'),
                    sector = kwargs.get('sector', None),
                    ticid = kwargs.get('ticid', None),
                    Apix_sigma = kwargs.get('Apix_sigma', 1.1))
    TESS.bads = kwargs.get('bads', False)
    TESS.pipeout()
    TESS.final()
    TESS.SaveData()
    return TESS.data
    #else:
    #    return np.load(os.path.join(outdir, '{}_data.npz'.format(re.findall('[0-9]+', tess_file)[3])))
class pipeline(Basecamp):
    def __init__(self, namefit, indir, outdir, **kwargs):
        self.indir = indir
        self.outdir = outdir
        self.fits = namefit
        self.name = kwargs.get('ticid', None) # re.findall('[0-9]+', self.fits)[3]
        self.S = kwargs.get('sector', None)
        self.ID = ast.literal_eval(self.name.lstrip('0'))
        self.object = 'TOI {}'.format(self.name)
        self.mission = kwargs.get('mission', 'tess')
        self.cadence = kwargs.get('cadence', 'lc').lower()
        if self.cadence == 'sc':
            kwargs.update({'optimize_gp': False})
        self.aperture_name = kwargs.get('aperture_name', 'automatic')
        self.sigma_aperture = kwargs.get('Apix_sigma', 2.0)
        pld_order = kwargs.get('pld_order', 3)
        assert (pld_order > 0), 'Invalid value for the de-trending order'
        self.pld_order = pld_order
        self.lambda_arr = kwargs.get('lambda_arr', 10 ** np.arange(0, 18, 0.5))
        if self.lambda_arr[0] != 0:
            self.lambda_arr = np.append(0, self.lambda_arr)
        self.leps = kwargs.get('leps', 0.05)
        self.osigma = kwargs.get('osigma', 5)
        self.oiter = kwargs.get('oiter', 10)
        self.cdivs = kwargs.get('cdivs', 3)
        self.giter = kwargs.get('giter', 3)
        self.gmaxf = kwargs.get('gmaxf', 200)
        self.optimize_gp = kwargs.get('optimize_gp', False)
        self.kernel_params = kwargs.get('kernel_params', None)
        self.kernel = kwargs.get('kernel', 'Basic')
        assert self.kernel in ['Basic', 'QuasiPeriodic'], 'Kwarg `kernel` must be one of `Basic` or `QuasiPeriodic`.'
        self.clobber_tpf = kwargs.get('clobber_tpf', False)
        self.bpad = kwargs.get('bpad', 100)
        self.max_pixels = kwargs.get('max_pixels', 75)
        self.saturation_tolerance = kwargs.get('saturation_tolerance', -0.1)
        self.gp_factor = kwargs.get('gp_factor', 100.)
        if kwargs.get('breakpoints', True):
            self.breakpoints = np.append(Breakpoints(self.ID, cadence = self.cadence, sector = ast.literal_eval(self.S)), [999999])
        else:
            self.breakpoints = np.array([999999])
        nseg = len(self.breakpoints)
        self.cv_min = kwargs.get('cv_min', 'mad')
        assert self.cv_min in ['mad', 'tv'], 'Invalid value for "cv_min".'
        self.cbv_num = kwargs.get('cbv_num', 1)
        self.cbv_niter = kwargs.get('cbv_niter', 50)
        self.cbv_win = kwargs.get('cbv_win', 999)
        self.cbv_order = kwargs.get('cbv_order', 3)
        self.lam_idx = -1
        self.lam = [[1e5] + [None for i in range(self.pld_order - 1)] for b in range(nseg)]
        self.reclam = None
        self.recmask = []
        self.X1N = None
        self.XCBV = [0, 1, 2, 3, 4]
        self.cdpp_arr = np.array([np.nan for b in range(nseg)])
        self.cdppr_arr = np.array([np.nan for b in range(nseg)])
        self.cdppv_arr = np.array([np.nan for b in range(nseg)])
        self.cdpp = np.nan
        self.cdppr = np.nan
        self.cdppv = np.nan
        self.cdppg = np.nan
        self.neighbors = []
        self._weights = None
    def load_tpf(self):
        data = GetData(self.ID, self.indir, self.outdir, fits = self.fits,
                       cadence = self.cadence, S = self.S,
                       aperture_name = self.aperture_name,
                       max_pixels = self.max_pixels,
                       saturation_tolerance = self.saturation_tolerance,
                       sav_aper_name = 'aperture_0')
        self.data = data
        self.time = data['time']
        self.fpix = data['fpix']
        self.fraw = np.sum(self.fpix, axis = 1)
        self.fpix_err = data['fpix_err']
        self.fraw_err = np.sqrt(np.sum(self.fpix_err ** 2, axis = 1))
        self.pixel_images = data['pixel_images']
        self.nanmask = data['nanmask']
        self.badmask = data['badmask']
        self.aperture = data['aperture']
        self.model = np.zeros_like(self.time)
        self.transitmask = np.array([], dtype = int)
        self.outmask = np.array([], dtype = int)
        self.breakpoints[-1] = len(self.time) - 1
        self.breakpoints = filter(None, self.breakpoints)
        self.get_norm()
    def pipeout(self):
        self.load_tpf()
        self.init_kernel()
        self.cdppr_arr = self.get_cdpp_arr()
        self.cdpp_arr = np.array(self.cdppr_arr)
        self.cdppv_arr = np.array(self.cdppr_arr)
        self.cdppr = self.get_cdpp()
        self.cdpp = self.cdppr
        self.cdppv = self.cdppr
        for n in range(self.pld_order):
            self.lam_idx += 1
            self.get_outliers()
            self.data['outliers_{}'.format(n + 1)] = self.outmask
            if n > 0 and self.optimize_gp:
                self.update_gp()
                self.data['kernel_params_LC{}'.format(n)] = self.kernel_params
            self.cross_validate(info = 'CV{}'.format(n))
            self.cdpp_arr = self.get_cdpp_arr()
            self.cdppv_arr *= self.cdpp_arr
            self.cdpp = self.get_cdpp()
            self.cdppv = np.nanmean(self.cdppv_arr)
            self.data['flux_LC{}'.format(n + 1)] = self.flux
            self.data['model_LC{}'.format(n)] = self.model
            self.data['cdpp_arr_LC{}'.format(n)] = self.cdpp_arr
            self.data['cdpp_LC{}'.format(n)] = self.cdpp
    def init_kernel(self):
        if self.kernel_params is None:
            X = self.apply_mask(self.fpix / self.flux.reshape(-1, 1))
            y = self.apply_mask(self.flux) - np.dot(X, np.linalg.solve(np.dot(X.T, X), np.dot(X.T, self.apply_mask(self.flux))))
            white = np.nanmedian([np.nanstd(c) for c in Chunks(y, 13)])
            amp = self.gp_factor * np.nanstd(y)
            tau = 30.0
            if self.kernel == 'Basic':
              self.kernel_params = [white, amp, tau]
            elif self.kernel == 'QuasiPeriodic':
              self.kernel_params = [white, amp, 1., 20.]
    def cross_validate(self, info = ''):
        for b, brkpt in enumerate(self.breakpoints):
            # print('Cross-validating chunk {}/{}...'.format(b + 1, len(self.breakpoints)))
            med_training = np.zeros_like(self.lambda_arr)
            med_validation = np.zeros_like(self.lambda_arr)
            m = self.get_masked_chunk(b)
            if len(m) < 3 * self.cdivs:
                self.cdppv_arr[b] = np.nan
                self.lam[b][self.lam_idx] = 0.
                continue
            time = self.time[m]
            flux = self.fraw[m]
            ferr = self.fraw_err[m]
            med = np.nanmedian(flux)
            validation = [[] for k, _ in enumerate(self.lambda_arr)]
            training = [[] for k, _ in enumerate(self.lambda_arr)]
            gp = GP(self.kernel, self.kernel_params, white = False)
            gp.compute(time, ferr)
            masks = list(Chunks(np.arange(0, len(time)), len(time) // self.cdivs))
            for i, mask in enumerate(masks):
                pre_t = self.cv_precompute([], b)
                pre_v = self.cv_precompute(mask, b)
                for k, lam in enumerate(self.lambda_arr):
                    self.lam[b][self.lam_idx] = lam
                    model = self.cv_compute(b, *pre_t)
                    training[k].append(self.fobj(flux - model, med, time, gp, mask))
                    model = self.cv_compute(b, *pre_v)
                    validation[k].append(self.fobj(flux - model, med, time, gp, mask))
            training = np.array(training)
            validation = np.array(validation)
            for k, _ in enumerate(self.lambda_arr):
                med_validation[k] = np.nanmean(validation[k])
                med_training[k] = np.nanmean(training[k])
            i = self.optimize_lambda(validation)
            v_best = med_validation[i]
            t_best = med_training[i]
            self.cdppv_arr[b] = v_best / t_best
            self.lam[b][self.lam_idx] = self.lambda_arr[i]
        self.compute()
    def get_outliers(self):
        M = lambda x: np.delete(x, np.concatenate([self.nanmask, self.badmask, self.transitmask]), axis = 0)
        t = M(self.time)
        outmask = [np.array([-1]), np.array(self.outmask)]
        while not np.array_equal(outmask[-2], outmask[-1]):
            if len(outmask) - 1 > self.oiter: break
            if np.any([np.array_equal(outmask[-1], i) for i in outmask[:-1]]): break
            self.compute()
            f = SavGol(M(self.flux))
            med = np.nanmedian(f)
            MAD = 1.4826 * np.nanmedian(np.abs(f - med))
            inds = np.where((f > med + self.osigma * MAD) | (f < med - self.osigma * MAD))[0]
            inds = np.array([np.argmax(self.time == t[i]) for i in inds])
            self.outmask = np.array(inds, dtype = int)
            outmask.append(np.array(inds))
    def fobj(self, y, y0, t, gp, mask):
        if self.cv_min == 'mad':
            gpm, _ = gp.predict(y - y0, t[mask])
            fdet = (y[mask] - gpm) / y0
            scatter = 1.e6 * (1.4826 * np.nanmedian(np.abs(fdet - np.nanmedian(fdet))) / np.sqrt(len(mask)))
            return scatter
        elif self.cv_min == 'tv':
            return 1.e6 * np.sum(np.abs(np.diff(y[mask]))) / len(mask) / y0
    def cv_precompute(self, mask, b):
        m1 = self.get_masked_chunk(b)
        flux = self.fraw[m1]
        K = GetCovariance(self.kernel, self.kernel_params, self.time[m1], self.fraw_err[m1])
        med = np.nanmedian(flux)
        M = lambda x, axis = 0: np.delete(x, mask, axis = axis)
        m2 = M(m1)
        mK = M(M(K, axis = 0), axis = 1)
        f = M(flux) - med
        A = [None for i in range(self.pld_order)]
        B = [None for i in range(self.pld_order)]
        for n in range(self.pld_order):
            if self.lam_idx >= n:
                X2 = self.X(n, m2)
                X1 = self.X(n, m1)
                A[n] = np.dot(X2, X2.T)
                B[n] = np.dot(X1, X2.T)
                del X1, X2
        return A, B, mK, f
    def cv_compute(self, b, A, B, mK, f):
        A = np.sum([l * a for l, a in zip(self.lam[b], A) if l is not None], axis = 0)
        B = np.sum([l * b for l, b in zip(self.lam[b], B) if l is not None], axis = 0)
        W = np.linalg.solve(mK + A, f)
        model = np.dot(B, W)
        model -= np.nanmedian(model)
        return model
    def optimize_lambda(self, validation):
        maxm = 0
        minr = len(validation)
        for n in range(validation.shape[1]):
            m = np.nanargmin(validation[:, n])
            if m > maxm:
                maxm = m
            r = np.where((validation[:, n] - validation[m, n]) /
                          validation[m, n] <= self.leps)[0][-1]
            if r < minr:
                minr = r
        return min(maxm, minr)
    def update_gp(self):
        self.kernel_params = GetKernelParams(self.time, self.flux, self.fraw_err,
                                             mask = self.mask, guess = self.kernel_params,
                                             giter = self.giter, gmaxf = self.gmaxf,
                                             kernel = self.kernel)
    def final(self):
        mask  = np.array(sorted(list(set(list(self.data['badmask'])))))
        time = np.delete(self.time, mask)
        flux = np.delete(self.flux, mask)
        ferr = np.delete(self.fraw_err, mask)
        zero_ind = np.where(ferr == 0.)[0]
        ferr[zero_ind] = 1.e-8
        if self.S == '1':
            time_array = np.array([[1347.34, 1349.51]])
        elif self.S == '3':
            time_array = np.array([[time[0], 1385.9],
                                   [1395.44, 1395.51]])
        else:
	        time_array = np.array([])
								   
        time_ind = np.array([], dtype = 'int')
        for interval in time_array:
            time_ind = np.append(time_ind, np.where((time >= interval[0]) & (time <= interval[1]))[0])
        res_time = time[time_ind]
        time = np.delete(time, time_ind)
        flux = np.delete(flux, time_ind)
        ferr = np.delete(ferr, time_ind)
        flux, ferr = Sf(time, flux, ferr, fraction_rate = 0.05, plot = 1, make_ylim = 0, outdir = self.outdir)
        self.data['time_flat'] = time
        self.data['flux_flat'] = flux
        self.data['ferr_flat'] = ferr
        time = np.insert(time, time_ind, res_time)
        flux = np.insert(flux, time_ind, 1.0)
        ferr = np.insert(ferr, time_ind, 0.001)
        try:
            self.data['bls_flag'], self.data['bls_periods'] = bl(time, flux, ferr, self.outdir)
        except:
            self.data['bls_flag'] = -1
            self.data['bls_periods'] = -1
    def SaveData(self):
        self.data.update(indir = self.indir, outdir = self.outdir, fraw = self.fraw,
                         fraw_err = self.fraw_err, breakpoints = self.breakpoints,
                         transitmask = self.transitmask, Q = self.S,
                         object = self.object)
        #np.savez_compressed(os.path.join(self.outdir, '{}_data.npz'.format(self.ID)), **self.data)
