"""PyInstaller hook for Prophet package."""

from PyInstaller.utils.hooks import collect_all, collect_data_files

# Collect all Prophet files including data files
datas, binaries, hiddenimports = collect_all('prophet')

# Make sure to include version file explicitly
prophet_datas = collect_data_files('prophet', include_py_files=True)
datas.extend(prophet_datas)

# Add cmdstanpy dependencies
cmdstanpy_datas = collect_data_files('cmdstanpy', include_py_files=True)
datas.extend(cmdstanpy_datas)

# Add required hidden imports
hiddenimports.extend([
    'prophet.__version__',
    'cmdstanpy._version',
    'prophet.make_holidays',
    'prophet.forecaster',
    'prophet.diagnostics',
    'prophet.plot',
    'prophet.serialize',
    'cmdstanpy.model',
    'cmdstanpy.stanfit',
    'holidays',
    'holidays.countries',
    'holidays.constants',
    'holidays.holiday_base',
    'holidays.utils',
    'hijri_converter',
    'korean_lunar_calendar',
    'convertdate',
    'lunarcalendar',
    'pymeeus',
])