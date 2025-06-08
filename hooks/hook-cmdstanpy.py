"""PyInstaller hook for cmdstanpy package."""

from PyInstaller.utils.hooks import collect_all

# Collect all cmdstanpy files including data files
datas, binaries, hiddenimports = collect_all('cmdstanpy')

# Make sure version file is included
hiddenimports.extend([
    'cmdstanpy._version',
    'cmdstanpy.model',
    'cmdstanpy.cmdstan_args',
    'cmdstanpy.compilation',
    'cmdstanpy.install_cmdstan',
    'cmdstanpy.install_cxx_toolchain',
    'cmdstanpy.progress',
    'cmdstanpy.stanfit',
    'cmdstanpy.stanfit.mcmc',
    'cmdstanpy.stanfit.mle',
    'cmdstanpy.stanfit.vb',
    'cmdstanpy.stanfit.metadata',
    'cmdstanpy.stanfit.runset',
    'cmdstanpy.utils',
    'cmdstanpy.utils.cmdstan',
    'cmdstanpy.utils.command',
    'cmdstanpy.utils.data_munging',
    'cmdstanpy.utils.filesystem',
    'cmdstanpy.utils.json',
    'cmdstanpy.utils.logging',
    'cmdstanpy.utils.stancsv',
])