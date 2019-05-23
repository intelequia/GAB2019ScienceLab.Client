#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .tess import CDPP
from .gp import GetCovariance, GetKernelParams
from scipy.linalg import block_diag
import os, sys
import numpy as np
from itertools import combinations_with_replacement as multichoose

class Basecamp(object):
    @property
    def flux(self):
        return self.fraw - self.model
    @property
    def norm(self):
        return self._norm
    @property
    def mask(self):
        return np.array(list(set(np.concatenate([self.outmask, self.badmask, self.transitmask, self.nanmask]))), dtype = int)
    def get_norm(self):
        self._norm = self.fraw
    def X(self, i, j = slice(None, None, None)):
        X1 = self.fpix[j] / self.norm[j].reshape(-1, 1)
        X = np.product(list(multichoose(X1.T, i + 1)), axis = 1).T
        if self.X1N is not None:
            return np.hstack([X, self.X1N[j] ** (i + 1)])
        else:
            return X
    def compute(self):
        model = [None for b in self.breakpoints]
        for b, brkpt in enumerate(self.breakpoints):
            m = self.get_masked_chunk(b)
            c = self.get_chunk(b)
            mK = GetCovariance(self.kernel, self.kernel_params, self.time[m], self.fraw_err[m])
            med = np.nanmedian(self.fraw[m])
            f = self.fraw[m] - med
            A = np.zeros((len(m), len(m)))
            B = np.zeros((len(c), len(m)))
            for n in range(self.pld_order):
                if (self.lam_idx >= n) and (self.lam[b][n] is not None):
                    XM = self.X(n, m)
                    XC = self.X(n, c)
                    A += self.lam[b][n] * np.dot(XM, XM.T)
                    B += self.lam[b][n] * np.dot(XC, XM.T)
                    del XM, XC
            W = np.linalg.solve(mK + A, f)
            model[b] = np.dot(B, W)
            del A, B, W
        if len(model) > 1:
            self.model = model[0][:-self.bpad]
            for m in model[1:-1]:
                i = 1
                while len(self.model) - i in self.mask:
                    i += 1
                offset = self.model[-i] - m[self.bpad - i]
                self.model = np.concatenate([self.model, m[self.bpad:-self.bpad] + offset])
            i = 1
            while len(self.model) - i in self.mask:
                i += 1
            offset = self.model[-i] - model[-1][self.bpad - i]
            self.model = np.concatenate([self.model, model[-1][self.bpad:] + offset])
        else:
            self.model = model[0]
        self.model -= np.nanmedian(self.model)
        self.cdpp_arr = self.get_cdpp_arr()
        self.cdpp = self.get_cdpp()
        self._weights = None
    def compute_joint(self):
        A = [None for b in self.breakpoints]
        B = [None for b in self.breakpoints]
        for b, brkpt in enumerate(self.breakpoints):
            m = self.get_masked_chunk(b, pad = False)
            c = self.get_chunk(b, pad = False)
            A[b] = np.zeros((len(m), len(m)))
            B[b] = np.zeros((len(c), len(m)))
            for n in range(self.pld_order):
                if (self.lam_idx >= n) and (self.lam[b][n] is not None):
                    XM = self.X(n, m)
                    XC = self.X(n, c)
                    A[b] += self.lam[b][n] * np.dot(XM, XM.T)
                    B[b] += self.lam[b][n] * np.dot(XC, XM.T)
                    del XM, XC
        BIGA = block_diag(*A)
        del A
        BIGB = block_diag(*B)
        del B
        mK = GetCovariance(self.kernel, self.kernel_params, self.apply_mask(self.time), self.apply_mask(self.fraw_err))
        f = self.apply_mask(self.fraw)
        f -= np.nanmedian(f)
        W = np.linalg.solve(mK + BIGA, f)
        self.model = np.dot(BIGB, W)
        self.model -= np.nanmedian(self.model)
        self.cdpp_arr = self.get_cdpp_arr()
        self.cdpp = self.get_cdpp()
        self._weights = None
    def apply_mask(self, x = None):
        if x is None:
            return np.delete(np.arange(len(self.time)), self.mask)
        else:
            return np.delete(x, self.mask, axis = 0)
    def get_chunk(self, b, x = None, pad = True):
        M = np.arange(len(self.time))
        if b > 0:
            res = M[(M > self.breakpoints[b - 1] - int(pad) * self.bpad) & (M <= self.breakpoints[b] + int(pad) * self.bpad)]
        else:
            res = M[M <= self.breakpoints[b] + int(pad) * self.bpad]
        if x is None:
            return res
        else:
            return x[res]
    def get_masked_chunk(self, b, x = None, pad = True):
        M = self.apply_mask(np.arange(len(self.time)))
        if b > 0:
            res = M[(M > self.breakpoints[b - 1] - int(pad) * self.bpad) & (M <= self.breakpoints[b] + int(pad) * self.bpad)]
        else:
            res = M[M <= self.breakpoints[b] + int(pad) * self.bpad]
        if x is None:
            return res
        else:
            return x[res]
    def get_weights(self):
        weights = [None for i in range(len(self.breakpoints))]
        for b, brkpt in enumerate(self.breakpoints):
            m = self.get_masked_chunk(b)
            c = self.get_chunk(b)
            _mK = GetCovariance(self.kernel, self.kernel_params, self.time[m], self.fraw_err[m])
            f = self.fraw[m] - np.nanmedian(self.fraw)
            _A = [None for i in range(self.pld_order)]
            for n in range(self.pld_order):
                if self.lam_idx >= n:
                    X = self.X(n, m)
                    _A[n] = np.dot(X, X.T)
                    del X
            A = np.sum([l * a for l, a in zip(self.lam[b], _A) if l is not None], axis = 0)
            W = np.linalg.solve(_mK + A, f)
            weights[b] = [l * np.dot(self.X(n, m).T, W) for n, l in enumerate(self.lam[b]) if l is not None]
        self._weights = weights
    def get_cdpp_arr(self, flux = None):
        if flux is None:
            flux = self.flux
        return np.array([CDPP(flux[self.get_masked_chunk(b)], cadence = self.cadence) for b, _ in enumerate(self.breakpoints)])
    def get_cdpp(self, flux = None):
        if flux is None:
            flux = self.flux
        return CDPP(self.apply_mask(flux), cadence = self.cadence)
