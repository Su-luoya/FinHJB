from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
REPO_URL = "https://github.com/Su-luoya/FinHJB"
PAGES_URL = "https://su-luoya.github.io/FinHJB/"
LANGUAGES = {
    "en": "English",
    "zh": "中文",
}

sys.path.insert(0, str(SRC_ROOT))


def _read_project_version() -> str:
    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.split("=", 1)[1].strip().strip('"')
    return "0.0.0"


project = "FinHJB"
author = "Haotian Deng"
copyright = "2026, Haotian Deng"
release = version = _read_project_version()

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

source_suffix = {
    ".md": "markdown",
}
root_doc = "en/index"
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
]
templates_path = ["_templates"]
html_static_path = ["_static"]

myst_heading_anchors = 3

autodoc_member_order = "bysource"
autodoc_class_signature = "mixed"
autodoc_typehints = "description"
add_module_names = False
napoleon_use_rtype = False

html_theme = "pydata_sphinx_theme"
html_title = "FinHJB"
html_baseurl = PAGES_URL
html_theme_options = {
    "logo": {
        "text": "FinHJB",
    },
    "navbar_center": [],
    "navbar_end": ["language-switcher", "theme-switcher", "navbar-icon-links"],
    "icon_links": [
        {
            "name": "GitHub",
            "url": REPO_URL,
            "icon": "fa-brands fa-github",
        }
    ],
    "show_prev_next": False,
}


def _resolve_language_target(docname: str, target_language: str, found_docs: set[str]) -> str:
    prefix = f"{target_language}/"
    if docname.startswith("en/") or docname.startswith("zh/"):
        suffix = docname.split("/", 1)[1]
        candidate = f"{target_language}/{suffix}"
        if candidate in found_docs:
            return candidate
    fallback = f"{target_language}/index"
    if fallback in found_docs:
        return fallback
    return next(doc for doc in sorted(found_docs) if doc.startswith(prefix))


def add_language_switcher_context(app, pagename, templatename, context, doctree) -> None:
    pathto = context["pathto"]
    found_docs = set(app.env.found_docs)
    current_language = next(
        (language for language in LANGUAGES if pagename.startswith(f"{language}/")),
        "en",
    )
    context["language_switcher"] = {
        "current_label": LANGUAGES.get(current_language, "Language"),
        "links": [
            {
                "code": language,
                "label": label,
                "href": pathto(_resolve_language_target(pagename, language, found_docs)),
                "current": language == current_language,
            }
            for language, label in LANGUAGES.items()
        ],
    }


def collect_redirect_pages(app):
    yield (
        "index",
        {
            "title": "FinHJB Documentation",
            "redirect_target": "./en/",
        },
        "redirect.html",
    )


def setup(app):
    app.add_css_file("language-switcher.css")
    app.connect("html-page-context", add_language_switcher_context)
    app.connect("html-collect-pages", collect_redirect_pages)
