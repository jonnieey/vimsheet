import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "VimSheet"
copyright = "2026, VimSheet Contributors"
author = "VimSheet Contributors"
version = "0.1.0"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.imgmath",
    "sphinx.ext.todo",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.githubpages",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.graphviz",
    "sphinx.ext.duration",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = ".rst"
master_doc = "index"
language = "en"
pygments_style = "sphinx"
highlight_language = "python3"
add_function_parentheses = True
add_module_names = True

default_role = "py:obj"

rst_epilog = """
.. |vimsheet| replace:: **VimSheet**
.. |version| replace:: 0.1.0
"""

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
    "member-order": "bysource",
}
autodoc_typehints = "description"
autodoc_mock_imports = []
autodoc_inherit_docstrings = True

autosummary_generate = True
autosummary_generate_overwrite = True
autosummary_imported_members = True
autosummary_ignore_module_all = False

napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_rtype = True
napoleon_attr_annotations = False
napoleon_preprocess_types = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "textual": ("https://textual.textualize.io/", None),
}
intersphinx_timeout = 30
intersphinx_cache_limit = 5

todo_include_todos = True
todo_emit_warnings = False

suppress_warnings = [
    "autosummary.import_cycle",
    "toc.secnum",
]
nitpicky = False

extlinks = {
    "issue": ("https://github.com/vimsheet/vimsheet/issues/%s", "GH#%s"),
    "pr": ("https://github.com/vimsheet/vimsheet/pull/%s", "PR #%s"),
    "commit": ("https://github.com/vimsheet/vimsheet/commit/%s", "commit %s"),
}

numfig = True
numfig_secnum_depth = 2

inheritance_graph_attrs = dict(rankdir="TB", size='"8.0, 12.0"', fontsize=14)
inheritance_node_attrs = dict(shape="box", style="rounded", fontsize=12)
inheritance_edge_attrs = dict(arrowsize=1.5)

graphviz_output_format = "svg"

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "sticky_navigation": True,
    "includehidden": True,
    "titles_only": False,
    "logo_only": False,
}
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_copy_source = True
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True
html_last_updated_fmt = "%Y-%m-%d %H:%M:%S"
html_use_index = True
html_split_index = False
html_context = {
    "display_github": True,
    "github_user": "vimsheet",
    "github_repo": "vimsheet",
    "github_version": "main",
    "conf_py_path": "/docs/source/",
}
htmlhelp_basename = "VimSheetDoc"

latex_elements = {
    "papersize": "a4paper",
    "pointsize": "10pt",
    "preamble": "",
    "figure_align": "H",
    "releasename": "Release",
    "tableofcontents": "",
    "fncychap": "\\usepackage[Bjornstrup]{fncychap}",
}
latex_documents = [
    (master_doc, "VimSheet.tex", "VimSheet Documentation", author, "manual", False),
]
latex_logo = ""
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_use_xindy = True

man_pages = [
    (master_doc, "vimsheet", "VimSheet Documentation", [author], 1),
]

texinfo_documents = [
    (
        master_doc,
        "PySheet",
        "PySheet Documentation",
        author,
        "VimSheet",
        "A vim-like TUI spreadsheet for the terminal",
        "Miscellaneous",
        False,
    ),
]

epub_title = project
epub_author = author
epub_publisher = author
epub_copyright = copyright
epub_language = language
epub_show_urls = "inline"
epub_basename = "PySheet"
epub_cover = ("", "")

locale_dirs = ["locale/"]
gettext_compact = False
gettext_location = True
gettext_uuid = False

tags = globals().get("tags")
if tags is not None and tags.has("offline"):
    mathjax_config = None
    extensions.remove("sphinx.ext.mathjax")
else:
    mathjax_config = {
        "tex2jax": {
            "inlineMath": [["$", "$"], ["\\(", "\\)"]],
            "displayMath": [["$$", "$$"], ["\\[", "\\]"]],
        }
    }
