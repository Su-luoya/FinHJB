from __future__ import annotations

import re
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
sys.setrecursionlimit(3000)


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
    "sphinx.ext.mathjax",
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
myst_enable_extensions = [
    "amsmath",
    "dollarmath",
]

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

_FENCE_START_RE = re.compile(r"^[ \t]*([`~]{3,})")
_INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1", re.DOTALL)
_DISPLAY_DELIMITER_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
_INLINE_DELIMITER_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)


def _rewrite_latex_math_delimiters(text: str) -> str:
    text = _DISPLAY_DELIMITER_RE.sub(
        lambda match: f"$$\n{match.group(1).strip(chr(10))}\n$$",
        text,
    )
    return _INLINE_DELIMITER_RE.sub(lambda match: f"${match.group(1)}$", text)


def _normalize_markdown_math_delimiters(text: str) -> str:
    chunks: list[str] = []
    buffer: list[str] = []
    in_fence = False
    fence_char = ""
    fence_length = 0

    def flush_buffer() -> None:
        if not buffer:
            return
        block = "".join(buffer)
        last_index = 0
        rewritten: list[str] = []
        for match in _INLINE_CODE_RE.finditer(block):
            rewritten.append(_rewrite_latex_math_delimiters(block[last_index : match.start()]))
            rewritten.append(match.group(0))
            last_index = match.end()
        rewritten.append(_rewrite_latex_math_delimiters(block[last_index:]))
        chunks.append("".join(rewritten))
        buffer.clear()

    for line in text.splitlines(keepends=True):
        fence_match = _FENCE_START_RE.match(line)
        if not in_fence and fence_match:
            flush_buffer()
            marker = fence_match.group(1)
            in_fence = True
            fence_char = marker[0]
            fence_length = len(marker)
            chunks.append(line)
            continue

        if in_fence:
            chunks.append(line)
            closing_match = _FENCE_START_RE.match(line)
            if closing_match:
                marker = closing_match.group(1)
                if marker[0] == fence_char and len(marker) >= fence_length:
                    in_fence = False
                    fence_char = ""
                    fence_length = 0
            continue

        buffer.append(line)

    flush_buffer()
    return "".join(chunks)


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


def normalize_markdown_math_source(app, docname, source) -> None:
    docpath = app.env.doc2path(docname, base=False)
    if not docpath.endswith(".md"):
        return
    source[0] = _normalize_markdown_math_delimiters(source[0])


def setup(app):
    app.add_css_file("language-switcher.css")
    app.connect("html-page-context", add_language_switcher_context)
    app.connect("html-collect-pages", collect_redirect_pages)
    app.connect("source-read", normalize_markdown_math_source)
