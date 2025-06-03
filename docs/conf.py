"""Configuration file for the Sphinx documentation builder.

This configuration file is specifically tailored for the Apple Health Monitor Dashboard
project, providing comprehensive documentation generation with Google-style docstring
support, modern themes, and advanced features for API documentation.

Key Features:
    - Google-style docstring support via Napoleon extension
    - Modern responsive theme with customizable options
    - Automatic API documentation generation from source code
    - Cross-referencing with external Python libraries
    - Support for Markdown files alongside reStructuredText
    - Copy-button support for code examples
    - Mathematical notation support via MathJax
    - Interactive design elements and admonitions

The configuration automatically detects and includes optional extensions for enhanced
functionality while maintaining compatibility when they're not available.

For complete Sphinx configuration options, see:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import os
import sys
from pathlib import Path

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document) are in another directory, add these
# directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute.
sys.path.insert(0, os.path.abspath('../src'))

# -- Project information -----------------------------------------------------

project = 'Apple Health Monitor'
copyright = '2024, Apple Health Monitor Team'
author = 'Apple Health Monitor Team'

# The full version, including alpha/beta/rc tags
release = '0.1.0'
version = '0.1.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.githubpages',
]

# Optional extensions - only load if available
try:
    import myst_parser
    extensions.append('myst_parser')
except ImportError:
    pass

try:
    import sphinx_copybutton
    extensions.append('sphinx_copybutton')
except ImportError:
    pass

try:
    import sphinx_design
    extensions.append('sphinx_design')
except ImportError:
    pass

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The suffix(es) of source filenames.
if 'myst_parser' in extensions:
    source_suffix = {
        '.rst': None,
        '.md': 'myst_parser',
    }
else:
    source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  See the documentation for a list of options available for each theme.
html_theme_options = {
    'canonical_url': '',
    'analytics_id': '',
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 4,
    'includehidden': True,
    'titles_only': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}

# -- Extension configuration -------------------------------------------------

# -- Options for autodoc extension -------------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Don't show typehints in the signature
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"

# -- Options for autosummary extension ---------------------------------------

autosummary_generate = True
autosummary_generate_overwrite = True

# -- Options for napoleon extension ------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# -- Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'pandas': ('https://pandas.pydata.org/docs/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
    'pyqt6': ('https://www.riverbankcomputing.com/static/Docs/PyQt6/', None),
}

# -- Options for todo extension ----------------------------------------------

todo_include_todos = True

# -- Options for MyST parser ------------------------------------------------

if 'myst_parser' in extensions:
    myst_enable_extensions = [
        "amsmath",
        "colon_fence",
        "deflist",
        "dollarmath",
        "html_admonition",
        "html_image",
        "linkify",
        "replacements",
        "smartquotes",
        "substitution",
        "tasklist",
    ]

# -- Options for copybutton extension ---------------------------------------

if 'sphinx_copybutton' in extensions:
    copybutton_prompt_text = r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
    copybutton_prompt_is_regexp = True

# -- Custom configuration ---------------------------------------------------

# Add custom CSS
def setup(app):
    app.add_css_file('custom.css')

# HTML context for templates
html_context = {
    'display_github': True,
    'github_user': 'apple-health-monitor',
    'github_repo': 'health-monitor',
    'github_version': 'main/',
    'conf_py_path': '/docs/',
}

# Additional options
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

# Custom roles
rst_prolog = """
.. role:: python(code)
   :language: python
   :class: highlight
"""