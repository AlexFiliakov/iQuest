---
task_id: T01_S07
sprint_sequence_id: S07
status: open
complexity: High
last_updated: 2025-01-06T00:00:00Z
---

# Task: PyInstaller Configuration and Spec File Setup

## Description
Create and configure the PyInstaller specification file for building the Apple Health Monitor Dashboard executable. This task establishes the foundation for packaging the application as a Windows executable with proper resource bundling, hidden imports configuration, and optimization settings as defined in ADR-003.

## Goal / Objectives
- Create a comprehensive PyInstaller spec file based on ADR-003 template
- Configure all necessary hidden imports for PyQt6, matplotlib, pandas, and other dependencies
- Set up proper resource bundling for assets (fonts, images, configs)
- Implement executable metadata and icon (heart on fire emoji: ❤️‍🔥)
- Optimize for size and performance

## Related Documentation
- ADR-003: Packaging and Distribution Strategy
- Sprint S07 Meta File

## Acceptance Criteria
- [ ] PyInstaller spec file created with all required configurations
- [ ] Heart on fire icon created and properly embedded
- [ ] All hidden imports identified and configured
- [ ] Resource paths work correctly in bundled executable
- [ ] Version information from version.py is embedded
- [ ] Build process produces working executable
- [ ] Executable size is optimized (exclusions applied)

## Subtasks
- [ ] Create base PyInstaller spec file from ADR-003 template
- [ ] Generate heart on fire icon (❤️‍🔥) in .ico format
- [ ] Configure hidden imports for all dependencies
- [ ] Set up asset bundling (fonts, images, configs)
- [ ] Configure exclusions for size optimization
- [ ] Add version metadata embedding
- [ ] Create initial build script (build.py)
- [ ] Test basic executable generation
- [ ] Document any additional hidden imports discovered

## Implementation Guidance

### Icon Creation
The heart on fire emoji (❤️‍🔥) needs to be converted to a Windows .ico file:
- Use high-quality rendering at multiple resolutions (16x16, 32x32, 48x48, 256x256)
- Consider using a tool like ImageMagick or online converters
- Ensure transparency is preserved

### Hidden Imports
Based on ADR-003, include these hidden imports:
```python
hiddenimports = [
    'PyQt6.QtPrintSupport',
    'matplotlib.backends.backend_qt5agg',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.tslibs.offsets',
    'pandas._libs.tslibs.parsing',
    'pandas._libs.tslibs.timestamps',
    'pandas._libs.tslibs.timezones',
    'pandas._libs.tslibs.tzconversion',
    'pandas._libs.tslibs.fields',
    'pandas._libs.tslibs.holiday',
    'pandas._libs.tslibs.frequencies',
    'pandas._libs.tslibs.conversion',
    'pandas._libs.tslibs.strptime',
    'pandas._libs.tslibs.vectorized',
    'pandas._libs.tslibs.period',
    'pandas._libs.tslibs.dtypes',
    'pandas._libs.window.aggregations',
    'pandas._libs.window.indexers',
    'pandas._libs.properties',
    'pandas._libs.reshape',
    'pandas._libs.sparse',
    'pandas._libs.indexing',
    'pandas._libs.index',
    'pandas._libs.algos',
    'pandas._libs.join',
    'pandas._libs.hashing',
    'pandas._libs.missing',
    'pandas._libs.reduction',
    'pandas._libs.ops',
    'pandas._libs.lib',
    'pandas._libs.internals',
    'pandas._libs.parsers',
    'pandas._libs.tslib',
    'pandas._libs.hashtable',
    'pandas._libs.arrays',
    'pandas._libs.json',
    'pandas._libs.sparse',
    'pandas._libs.reduction',
    'pandas._libs.indexing',
    'pandas._libs.internals',
    'pandas._libs.writers',
    'pandas._libs.window',
    'pandas._libs.groupby',
    'scipy.special._ufuncs_cxx',
    'scipy.linalg.cython_blas',
    'scipy.linalg.cython_lapack',
    'scipy.integrate',
    'scipy.integrate.quadrature',
    'scipy.integrate.odepack',
    'scipy.integrate._odepack_py',
    'scipy.integrate.quadpack',
    'scipy.integrate._quadpack_py',
    'scipy.integrate._ode',
    'scipy.integrate.vode',
    'scipy.integrate._dop',
    'scipy.integrate.lsoda',
    'scipy.optimize._minpack',
    'scipy.optimize._zeros',
    'scipy.optimize.minpack2',
    'scipy.optimize._lbfgsb',
    'scipy.optimize._cobyla',
    'scipy.optimize._slsqp',
    'scipy.optimize._minpack',
    'scipy.optimize._lbfgsb',
    'scipy.optimize._zeros',
    'scipy.optimize._trustregion_constr',
    'scipy.optimize._differentialevolution',
    'scipy.optimize._linesearch',
    'scipy.optimize._hessian_update_strategy',
    'scipy.optimize._differentiable_functions',
    'scipy.optimize._constraints',
    'scipy.optimize._minimize',
    'scipy.optimize._trustregion_dogleg',
    'scipy.optimize._trustregion_ncg',
    'scipy.optimize._trustregion_krylov',
    'scipy.optimize._trustregion_exact',
    'scipy.optimize._trustregion_constr',
    'sqlalchemy.sql.default_comparator',
    'sqlalchemy.ext.baked',
]
```

### Exclusions for Size Optimization
```python
excludes = [
    'tkinter',
    'unittest',
    'pip',
    'setuptools',
    'wheel',
    'pytest',
    'notebook',
    'jupyter',
    'IPython',
]
```

### Resource Bundling
Ensure these directories are included:
- `assets/` - fonts and images
- Any default configuration files
- Database schema files if needed

## Output Log
*(This section is populated as work progresses on the task)*

[YYYY-MM-DD HH:MM:SS] Task created
