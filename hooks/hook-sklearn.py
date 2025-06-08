"""
PyInstaller hook for scikit-learn 1.5.x compatibility
"""

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Collect all sklearn submodules
hiddenimports = collect_submodules('sklearn')

# Add specific imports for sklearn 1.5.x that might be missed
hiddenimports += [
    'sklearn.utils._param_validation',
    'sklearn.utils._typedefs',
    'sklearn.utils._cython_blas',
    'sklearn.utils._weight_vector',
    'sklearn.neighbors._typedefs',
    'sklearn.neighbors._quad_tree',
    'sklearn.tree._utils',
    'sklearn.metrics._pairwise_distances_reduction',
    'sklearn.metrics._pairwise_distances_reduction._datasets_pair',
    'sklearn.metrics._pairwise_distances_reduction._middle_term_computer',
    'sklearn.preprocessing._csr_polynomial_expansion',
    'sklearn.preprocessing._target_encoder_fast',
    'sklearn.cluster._k_means_common',
    'sklearn.cluster._k_means_lloyd',
    'sklearn.cluster._k_means_elkan',
    'sklearn.cluster._k_means_minibatch',
    'sklearn.linear_model._cd_fast',
    'sklearn.linear_model._sgd_fast',
    'sklearn.linear_model._sag_fast',
    'sklearn.svm._libsvm',
    'sklearn.svm._liblinear',
    'sklearn.svm._libsvm_sparse',
    'sklearn.ensemble._gradient_boosting',
    'sklearn.ensemble._hist_gradient_boosting',
    'sklearn.decomposition._online_lda_fast',
    'sklearn.decomposition._cd_fast',
]

# Ensure joblib is included (sklearn dependency)
hiddenimports += [
    'joblib',
    'joblib.externals.loky',
    'joblib.externals.loky.backend',
    'joblib.externals.cloudpickle',
]

# Collect data files
datas = collect_data_files('sklearn')