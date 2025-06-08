"""
PyInstaller hook for pandas 2.2.x compatibility
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all pandas submodules
hiddenimports = collect_submodules('pandas')

# Add specific imports for pandas 2.2.x that might be missed
hiddenimports += [
    'pandas._libs.tslibs.ccalendar',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.base',
    'pandas._libs.interval',
    'pandas._libs.join',
    'pandas._libs.lib',
    'pandas._libs.missing',
    'pandas._libs.reduction',
    'pandas._libs.testing',
    'pandas._libs.writers',
    'pandas._libs.sparse',
    'pandas._libs.ops',
    'pandas._libs.ops_dispatch',
    'pandas._libs.properties',
    'pandas._libs.reshape',
    'pandas._libs.groupby',
    'pandas._libs.index',
    'pandas._libs.indexing',
    'pandas._libs.internals',
    'pandas._libs.parsers',
    'pandas._libs.algos',
    'pandas._libs.arrays',
    'pandas._libs.hashtable',
    'pandas._libs.json',
    'pandas.io.formats.style',
    'pandas.io.formats.style_render',
    'pandas.plotting._core',
    'pandas.plotting._matplotlib',
]

# Collect data files
datas = collect_data_files('pandas')