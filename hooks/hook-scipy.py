"""
PyInstaller hook for scipy 1.14.x compatibility
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all scipy submodules
hiddenimports = collect_submodules('scipy')

# Add specific imports for scipy 1.14.x that might be missed
hiddenimports += [
    'scipy._lib.array_api_compat',
    'scipy._lib.array_api_compat.numpy',
    'scipy._lib.array_api_compat.numpy.fft',
    'scipy._lib.array_api_compat.numpy.linalg',
    'scipy._lib._util',
    'scipy._lib._ccallback',
    'scipy._lib._ccallback_c',
    'scipy._lib._test_ccallback',
    'scipy._lib.messagestream',
    'scipy._lib._pep440',
    'scipy._lib._testutils',
    'scipy._lib._threadsafety',
    'scipy._lib._array_api',
    'scipy._lib._bunch',
    'scipy._lib._docscrape',
    'scipy._lib._gcutils',
    'scipy._lib.decorator',
    'scipy._distributor_init',
    'scipy.__config__',
    'scipy.version',
]

# Collect data files
datas = collect_data_files('scipy')