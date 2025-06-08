"""
PyInstaller hook for numpy 1.26.x compatibility
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all numpy submodules
hiddenimports = collect_submodules('numpy')

# Add specific imports for numpy 1.26.x that might be missed
hiddenimports += [
    'numpy._core',
    'numpy._core._multiarray_umath',
    'numpy.core._multiarray_umath',
    'numpy.random._bounded_integers',
    'numpy.random._common', 
    'numpy.random._generator',
    'numpy.random._mt19937',
    'numpy.random._pcg64',
    'numpy.random._philox',
    'numpy.random._sfc64',
    'numpy.random.bit_generator',
    'numpy.random.mtrand',
    'numpy._typing',
    'numpy._typing._ufunc',
]

# Collect data files
datas = collect_data_files('numpy')