"""
PyInstaller hook for jaraco packages
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all jaraco submodules
hiddenimports = collect_submodules('jaraco')

# Also explicitly include commonly needed jaraco modules
hiddenimports += [
    'jaraco.text',
    'jaraco.classes', 
    'jaraco.context',
    'jaraco.functools',
    'jaraco.collections',
    'jaraco.itertools',
]

# Collect any data files
datas = collect_data_files('jaraco')