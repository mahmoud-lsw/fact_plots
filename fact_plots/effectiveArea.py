#!/usr/bin/env python3
# from __future__ import print_function
import numpy as np
import matplotlib
import datetime
# matplotlib.rc_file("./matplotlibrc")
# matplotlib.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from docopt import docopt
import logging
import pandas as pd

logger  = logging.getLogger(__name__)

def integrateEnergySpectrum(e_min, e_max, gamma):
    upper = np.power( e_max, gamma+1) / (gamma+1)
    lower = np.power( e_min, gamma+1) / (gamma+1)
    return upper-lower

def calculate_a_eff_bin(n_trigger, max_impact, E_bin_low, e_bin_high, E_min, E_max, gamma, nCorsika = 12e6):
    N_0 =   nCorsika
    N_0 *=  integrateEnergySpectrum(E_bin_low, e_bin_high, gamma)
    N_0 /=  integrateEnergySpectrum(E_min, E_max, gamma)

    return n_trigger / N_0 * np.pi * max_impact**2

def calc_a_eff(e_mc, nBins, min_e=None, max_e=None, max_impact=270, gamma=-2.7, nCorsika = 12e6):
    """Calculates the effective collection area for each given energy bin

    Keyword arguments:

    e_mc -- monte carlo energy

    nBins        -- number of energy bins in range

    min_e       -- min. simulated energy in GeV

    max_e       -- max. simulated energy in GeV

    max_impact  -- maximally simulated impact parameter in m

    gamma       -- spectral index
    """

    if min_e is None:
        min_e = np.min(e_mc)
    if max_e is None:
        max_e = np.max(e_mc)

    logger.info("Energy range {} GeV to {} GeV".format(min_e, max_e))
    logger.info("Number of bins: {}".format(nBins))


    bins = np.logspace(np.log10(min_e), np.log10(max_e), nBins)
    logger.debug("Bin width: {}".format(bins))

    bin_middles = np.empty(nBins)
    bin_middles[:] = np.nan
    bin_widths = np.empty(nBins)
    bin_widths[:] = np.nan

    A_eff = np.empty(nBins)
    A_eff[:] = np.nan

    A_eff_err = np.empty(nBins)
    A_eff_err[:] = np.nan

    n_trigger = np.empty(nBins)
    n_trigger[:] = np.nan

    # bin_low_edge  = min_e
    # bin_high_edge = 0

    for i in range(1, nBins):
        bin_low_edge  = bins[i-1]
        bin_high_edge = bins[i]
        if bin_high_edge > max_e:
            bin_high_edge = max_e
        #sum up all prio bin widths

        mask1 = e_mc < bin_high_edge
        mask2 = e_mc >= bin_low_edge

        mask = np.logical_and(mask1, mask2)

        if np.sum(mask) <= 1:
            logger.info("no entries for given mask {} <= emc < {}".format( '%.2E' % bin_low_edge, '%.2E' % bin_high_edge))
            continue

        bin_widths[i]  = (bin_high_edge - bin_low_edge)
        bin_middles[i] = bin_low_edge + bin_widths[i]/2

        energy_bin = e_mc[mask]
        #print(energy_bin)
        n_trigger[i] = np.sum(mask)

        logger.debug("Sum(mask)={}, len(energy_bin)={}".format(n_trigger[i], len(energy_bin) ))

        A_eff[i] = calculate_a_eff_bin(n_trigger[i], max_impact,
                                        bin_low_edge, bin_high_edge,
                                        min_e, max_e, gamma, nCorsika)
        #A_eff[i] *= np.sum(energy_bin)

        A_eff_err[i] = np.sqrt(n_trigger[i])

        logger.debug("Aeff={}m², N_tr = {}, range {} <= emc < {}, bin width={}".format(
                                        '%.2E' % A_eff[i],
                                        '%.2E' % n_trigger[i],
                                        '%.2E' % bin_low_edge,
                                        '%.2E' % bin_high_edge,
                                        '%.2E' % bin_widths[i],
                                        ))

    return_dict = dict(
        range       = np.array([min_e,max_e]),
        Aeff        = np.array(A_eff),
        Aeff_res    = np.array(A_eff_err),
        nTrigger    = np.array(n_trigger),
        bin_middles = np.array(bin_middles),
        bin_widths = np.array(bin_widths),
        bins   = np.array(bins)
    )

    return return_dict

def plot_eff_area(ax, e_mc, label="1" ):
    effectiveArea = calc_a_eff(e_mc, 20, min_e=200, max_e=50e3)


    ax.errorbar(effectiveArea["bin_middles"],
                effectiveArea["Aeff"],
                xerr=effectiveArea["bin_widths"]/2,
                yerr=effectiveArea["Aeff_res"],
                fmt="o", label=label)

    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlabel("log10(E / GeV)")
    ax.set_ylabel("log10(A_eff / mˆ2)")

    return effectiveArea

def plot_nTriggers(ax, effA_result, label="1" ):

    ax.errorbar(effA_result["bin_middles"],
                effA_result["nTrigger"],
                xerr=effA_result["bin_widths"]/2,
                yerr=np.sqrt(effA_result["nTrigger"]),
                fmt="o", label=label)

    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlabel("log10(E / GeV)")
    ax.set_ylabel("log10(number of triggers)")
