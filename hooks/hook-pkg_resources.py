"""
PyInstaller hook for pkg_resources
Fixes jaraco.text import issues and NullProvider attribute
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

# Collect all pkg_resources submodules
hiddenimports = collect_submodules('pkg_resources')

# Ensure jaraco packages are included
hiddenimports += [
    'jaraco',
    'jaraco.text',
    'jaraco.classes',
    'jaraco.context', 
    'jaraco.functools',
    'jaraco.collections',
    'jaraco.itertools',
    'pkg_resources.extern',
    'pkg_resources._vendor',
    'pkg_resources._vendor.jaraco',
    'pkg_resources._vendor.jaraco.text',
    'pkg_resources._vendor.jaraco.context',
    'pkg_resources._vendor.jaraco.functools',
    'pkg_resources._vendor.jaraco.classes',
    'pkg_resources._vendor.more_itertools',
    'more_itertools',
    'inflect',
]

# Copy metadata and data files
datas = []

# Copy metadata for packages that need it
for pkg in ['setuptools', 'pkg_resources', 'jaraco.text', 'jaraco.classes', 'jaraco.context', 'jaraco.functools']:
    try:
        datas.extend(copy_metadata(pkg))
    except:
        pass

# Copy data files
try:
    datas.extend(collect_data_files('pkg_resources'))
except:
    pass