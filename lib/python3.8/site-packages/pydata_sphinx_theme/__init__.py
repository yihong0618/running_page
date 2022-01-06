"""
Bootstrap-based sphinx theme from the PyData community
"""
import os

from sphinx.errors import ExtensionError
from sphinx.util import logging
from sphinx.environment.adapters.toctree import TocTree
from sphinx import addnodes

import jinja2
from bs4 import BeautifulSoup as bs

from .bootstrap_html_translator import BootstrapHTML5Translator

__version__ = "0.7.2"

logger = logging.getLogger(__name__)


def update_config(app, env):
    theme_options = app.config["html_theme_options"]
    if theme_options.get("search_bar_position") == "navbar":
        logger.warn(
            (
                "Deprecated config `search_bar_position` used."
                "Use `search-field.html` in `navbar_end` template list instead."
            )
        )
    if not isinstance(theme_options.get("icon_links", []), list):
        raise ExtensionError(
            (
                "`icon_links` must be a list of dictionaries, you provided "
                f"type {type(theme_options.get('icon_links'))}."
            )
        )


def update_templates(app, pagename, templatename, context, doctree):
    """Update template names for page build."""
    template_sections = [
        "theme_navbar_start",
        "theme_navbar_center",
        "theme_navbar_end",
        "theme_footer_items",
        "theme_page_sidebar_items",
        "sidebars",
    ]

    for section in template_sections:
        if context.get(section):
            # Break apart `,` separated strings so we can use , in the defaults
            if isinstance(context.get(section), str):
                context[section] = [
                    ii.strip() for ii in context.get(section).split(",")
                ]

            # Add `.html` to templates with no suffix
            for ii, template in enumerate(context.get(section)):
                if not os.path.splitext(template)[1]:
                    context[section][ii] = template + ".html"


def add_toctree_functions(app, pagename, templatename, context, doctree):
    """Add functions so Jinja templates can add toctree objects."""

    def generate_nav_html(kind, startdepth=None, **kwargs):
        """
        Return the navigation link structure in HTML. Arguments are passed
        to Sphinx "toctree" function (context["toctree"] below).

        We use beautifulsoup to add the right CSS classes / structure for bootstrap.

        See https://www.sphinx-doc.org/en/master/templating.html#toctree.

        Parameters
        ----------
        kind : ["navbar", "sidebar", "raw"]
            The kind of UI element this toctree is generated for.
        startdepth : int
            The level of the toctree at which to start. By default, for
            the navbar uses the normal toctree (`startdepth=0`), and for
            the sidebar starts from the second level (`startdepth=1`).
        kwargs: passed to the Sphinx `toctree` template function.

        Returns
        -------
        HTML string (if kind in ["navbar", "sidebar"])
        or BeautifulSoup object (if kind == "raw")
        """
        if startdepth is None:
            startdepth = 1 if kind == "sidebar" else 0

        if startdepth == 0:
            toc_sphinx = context["toctree"](**kwargs)
        else:
            # select the "active" subset of the navigation tree for the sidebar
            toc_sphinx = index_toctree(app, pagename, startdepth, **kwargs)

        soup = bs(toc_sphinx, "html.parser")

        # pair "current" with "active" since that's what we use w/ bootstrap
        for li in soup("li", {"class": "current"}):
            li["class"].append("active")

        # Remove navbar/sidebar links to sub-headers on the page
        for li in soup.select("li"):
            # Remove
            if li.find("a"):
                href = li.find("a")["href"]
                if "#" in href and href != "#":
                    li.decompose()

        if kind == "navbar":
            # Add CSS for bootstrap
            for li in soup("li"):
                li["class"].append("nav-item")
                li.find("a")["class"].append("nav-link")
            # only select li items (not eg captions)
            out = "\n".join([ii.prettify() for ii in soup.find_all("li")])

        elif kind == "sidebar":
            # Add bootstrap classes for first `ul` items
            for ul in soup("ul", recursive=False):
                ul.attrs["class"] = ul.attrs.get("class", []) + ["nav", "bd-sidenav"]

            # Add icons and labels for collapsible nested sections
            _add_collapse_checkboxes(soup)

            out = soup.prettify()

        elif kind == "raw":
            out = soup

        return out

    def generate_toc_html(kind="html"):
        """Return the within-page TOC links in HTML."""

        if "toc" not in context:
            return ""

        soup = bs(context["toc"], "html.parser")

        # Add toc-hN + visible classes
        def add_header_level_recursive(ul, level):
            if ul is None:
                return
            if level <= (context["theme_show_toc_level"] + 1):
                ul["class"] = ul.get("class", []) + ["visible"]
            for li in ul("li", recursive=False):
                li["class"] = li.get("class", []) + [f"toc-h{level}"]
                add_header_level_recursive(li.find("ul", recursive=False), level + 1)

        add_header_level_recursive(soup.find("ul"), 1)

        # Add in CSS classes for bootstrap
        for ul in soup("ul"):
            ul["class"] = ul.get("class", []) + ["nav", "section-nav", "flex-column"]

        for li in soup("li"):
            li["class"] = li.get("class", []) + ["nav-item", "toc-entry"]
            if li.find("a"):
                a = li.find("a")
                a["class"] = a.get("class", []) + ["nav-link"]

        # If we only have one h1 header, assume it's a title
        h1_headers = soup.select(".toc-h1")
        if len(h1_headers) == 1:
            title = h1_headers[0]
            # If we have no sub-headers of a title then we won't have a TOC
            if not title.select(".toc-h2"):
                out = ""
            else:
                out = title.find("ul").prettify()
        # Else treat the h1 headers as sections
        else:
            out = soup.prettify()

        # Return the toctree object
        if kind == "html":
            return out
        else:
            return soup

    # TODO: Deprecate in v0.7.0
    def get_nav_object(maxdepth=None, collapse=True, includehidden=True, **kwargs):
        """Return a list of nav links that can be accessed from Jinja.

        Parameters
        ----------
        maxdepth: int
            How many layers of TocTree will be returned
        collapse: bool
            Whether to only include sub-pages of the currently-active page,
            instead of sub-pages of all top-level pages of the site.
        kwargs: key/val pairs
            Passed to the `toctree` Sphinx method
        """
        if context["master_doc"] == pagename:
            logger.warn("`get_nav_object` is deprecated and will be removed in v0.7.0")

        toc_sphinx = context["toctree"](
            maxdepth=maxdepth, collapse=collapse, includehidden=includehidden, **kwargs
        )
        soup = bs(toc_sphinx, "html.parser")

        # # If no toctree is defined (AKA a single-page site), skip this
        # if toctree is None:
        #     return []

        nav_object = soup_to_python(soup, only_pages=True)

        return nav_object

    # TODO: Deprecate in v0.7.0
    def get_page_toc_object():
        """Return a list of within-page TOC links that can be accessed from Jinja."""

        if context["master_doc"] == pagename:
            logger.warn(
                ("`get_page_toc_object` is deprecated and will be " "removed in v0.7.0")
            )

        if "toc" not in context:
            return ""

        soup = bs(context["toc"], "html.parser")

        try:
            toc_object = soup_to_python(soup, only_pages=False)
        except Exception:
            return []

        # If there's only one child, assume we have a single "title" as top header
        # so start the TOC at the first item's children (AKA, level 2 headers)
        if len(toc_object) == 1:
            return toc_object[0]["children"]
        else:
            return toc_object

    def navbar_align_class():
        """Return the class that aligns the navbar based on config."""
        align = context.get("theme_navbar_align", "content")
        align_options = {
            "content": ("col-lg-9", "mr-auto"),
            "left": ("", "mr-auto"),
            "right": ("", "ml-auto"),
        }
        if align not in align_options:
            raise ValueError(
                (
                    "Theme optione navbar_align must be one of"
                    f"{align_options.keys()}, got: {align}"
                )
            )
        return align_options[align]

    def generate_google_analytics_script(id):
        """Handle the two types of google analytics id."""
        if id:
            if "G-" in id:
                script = f"""
                <script
                    async
                    src='https://www.googletagmanager.com/gtag/js?id={id}'
                ></script>
                <script>
                    window.dataLayer = window.dataLayer || [];
                    function gtag(){{ dataLayer.push(arguments); }}
                    gtag('js', new Date());
                    gtag('config', '{id}');
                </script>
                """
            else:
                script = f"""
                    <script
                        async
                        src='https://www.google-analytics.com/analytics.js'
                    ></script>
                    <script>
                        window.ga = window.ga || function () {{
                            (ga.q = ga.q || []).push(arguments) }};
                        ga.l = +new Date;
                        ga('create', '{id}', 'auto');
                        ga('set', 'anonymizeIp', true);
                        ga('send', 'pageview');
                    </script>
                """
            soup = bs(script, "html.parser")
            return soup
        else:
            return ""

    context["generate_nav_html"] = generate_nav_html
    context["generate_toc_html"] = generate_toc_html
    context["get_nav_object"] = get_nav_object
    context["get_page_toc_object"] = get_page_toc_object
    context["navbar_align_class"] = navbar_align_class
    context["generate_google_analytics_script"] = generate_google_analytics_script


def _add_collapse_checkboxes(soup):
    # based on https://github.com/pradyunsg/furo

    toctree_checkbox_count = 0

    for element in soup.find_all("li", recursive=True):
        # We check all "li" elements, to add a "current-page" to the correct li.
        classes = element.get("class", [])

        # Nothing more to do, unless this has "children"
        if not element.find("ul"):
            continue

        # Add a class to indicate that this has children.
        element["class"] = classes + ["has-children"]

        # We're gonna add a checkbox.
        toctree_checkbox_count += 1
        checkbox_name = f"toctree-checkbox-{toctree_checkbox_count}"

        # Add the "label" for the checkbox which will get filled.
        if soup.new_tag is None:
            continue
        label = soup.new_tag("label", attrs={"for": checkbox_name})
        label.append(soup.new_tag("i", attrs={"class": "fas fa-chevron-down"}))
        element.insert(1, label)

        # Add the checkbox that's used to store expanded/collapsed state.
        checkbox = soup.new_tag(
            "input",
            attrs={
                "type": "checkbox",
                "class": ["toctree-checkbox"],
                "id": checkbox_name,
                "name": checkbox_name,
            },
        )
        # if this has a "current" class, be expanded by default
        # (by checking the checkbox)
        if "current" in classes:
            checkbox.attrs["checked"] = ""

        element.insert(1, checkbox)


def _get_local_toctree_for(
    self: TocTree, indexname: str, docname: str, builder, collapse: bool, **kwargs
):
    """Return the "local" TOC nodetree (relative to `indexname`)."""
    # this is a copy of `TocTree.get_toctree_for`, but where the sphinx version
    # always uses the "master" doctree:
    #     doctree = self.env.get_doctree(self.env.config.master_doc)
    # we here use the `indexname` additional argument to be able to use a subset
    # of the doctree (e.g. starting at a second level for the sidebar):
    #     doctree = app.env.tocs[indexname].deepcopy()

    doctree = self.env.tocs[indexname].deepcopy()

    toctrees = []
    if "includehidden" not in kwargs:
        kwargs["includehidden"] = True
    if "maxdepth" not in kwargs or not kwargs["maxdepth"]:
        kwargs["maxdepth"] = 0
    else:
        kwargs["maxdepth"] = int(kwargs["maxdepth"])
    kwargs["collapse"] = collapse

    for toctreenode in doctree.traverse(addnodes.toctree):
        toctree = self.resolve(docname, builder, toctreenode, prune=True, **kwargs)
        if toctree:
            toctrees.append(toctree)
    if not toctrees:
        return None
    result = toctrees[0]
    for toctree in toctrees[1:]:
        result.extend(toctree.children)
    return result


def index_toctree(app, pagename: str, startdepth: int, collapse: bool = True, **kwargs):
    """
    Returns the "local" (starting at `startdepth`) TOC tree containing the
    current page, rendered as HTML bullet lists.

    This is the equivalent of `context["toctree"](**kwargs)` in sphinx
    templating, but using the startdepth-local instead of global TOC tree.
    """
    # this is a variant of the function stored in `context["toctree"]`, which is
    # defined as `lambda **kwargs: self._get_local_toctree(pagename, **kwargs)`
    # with `self` being the HMTLBuilder and the `_get_local_toctree` basically
    # returning:
    #     return self.render_partial(TocTree(self.env).get_toctree_for(
    #         pagename, self, collapse, **kwargs))['fragment']

    if "includehidden" not in kwargs:
        kwargs["includehidden"] = False
    if kwargs.get("maxdepth") == "":
        kwargs.pop("maxdepth")

    toctree = TocTree(app.env)
    ancestors = toctree.get_toctree_ancestors(pagename)
    try:
        indexname = ancestors[-startdepth]
    except IndexError:
        # eg for index.rst, but also special pages such as genindex, py-modindex, search
        # those pages don't have a "current" element in the toctree, so we can
        # directly return an emtpy string instead of using the default sphinx
        # toctree.get_toctree_for(pagename, app.builder, collapse, **kwargs)
        return ""

    toctree_element = _get_local_toctree_for(
        toctree, indexname, pagename, app.builder, collapse, **kwargs
    )
    return app.builder.render_partial(toctree_element)["fragment"]


def soup_to_python(soup, only_pages=False):
    """
    Convert the toctree html structure to python objects which can be used in Jinja.

    Parameters
    ----------
    soup : BeautifulSoup object for the toctree
    only_pages : bool
        Only include items for full pages in the output dictionary. Exclude
        anchor links (TOC items with a URL that starts with #)

    Returns
    -------
    nav : list of dicts
        The toctree, converted into a dictionary with key/values that work
        within Jinja.
    """
    # toctree has this structure (caption only for toctree, not toc)
    #   <p class="caption">...</span></p>
    #   <ul>
    #       <li class="toctree-l1"><a href="..">..</a></li>
    #       <li class="toctree-l1"><a href="..">..</a></li>
    #       ...

    def extract_level_recursive(ul, navs_list):

        for li in ul.find_all("li", recursive=False):
            ref = li.a
            url = ref["href"]
            title = "".join(map(str, ref.contents))
            active = "current" in li.get("class", [])

            # If we've got an anchor link, skip it if we wish
            if only_pages and "#" in url and url != "#":
                continue

            # Converting the docutils attributes into jinja-friendly objects
            nav = {}
            nav["title"] = title
            nav["url"] = url
            nav["active"] = active

            navs_list.append(nav)

            # Recursively convert children as well
            nav["children"] = []
            ul = li.find("ul", recursive=False)
            if ul:
                extract_level_recursive(ul, nav["children"])

    navs = []
    for ul in soup.find_all("ul", recursive=False):
        extract_level_recursive(ul, navs)
    return navs


# -----------------------------------------------------------------------------


def setup_edit_url(app, pagename, templatename, context, doctree):
    """Add a function that jinja can access for returning the edit URL of a page."""

    def get_edit_url():
        """Return a URL for an "edit this page" link."""
        file_name = f"{pagename}{context['page_source_suffix']}"

        # Make sure that doc_path has a path separator only if it exists (to avoid //)
        doc_path = context.get("doc_path", "")
        if doc_path and not doc_path.endswith("/"):
            doc_path = f"{doc_path}/"

        default_provider_urls = {
            "bitbucket_url": "https://bitbucket.org",
            "github_url": "https://github.com",
            "gitlab_url": "https://gitlab.com",
        }

        edit_url_attrs = {}

        # ensure custom URL is checked first, if given
        url_template = context.get("edit_page_url_template")

        if url_template is not None:
            if "file_name" not in url_template:
                raise ExtensionError(
                    "Missing required value for `use_edit_page_button`. "
                    "Ensure `file_name` appears in `edit_page_url_template`: "
                    f"{url_template}"
                )

            edit_url_attrs[("edit_page_url_template",)] = url_template

        edit_url_attrs.update(
            {
                ("bitbucket_user", "bitbucket_repo", "bitbucket_version"): (
                    "{{ bitbucket_url }}/{{ bitbucket_user }}/{{ bitbucket_repo }}"
                    "/src/{{ bitbucket_version }}"
                    "/{{ doc_path }}{{ file_name }}?mode=edit"
                ),
                ("github_user", "github_repo", "github_version"): (
                    "{{ github_url }}/{{ github_user }}/{{ github_repo }}"
                    "/edit/{{ github_version }}/{{ doc_path }}{{ file_name }}"
                ),
                ("gitlab_user", "gitlab_repo", "gitlab_version"): (
                    "{{ gitlab_url }}/{{ gitlab_user }}/{{ gitlab_repo }}"
                    "/-/edit/{{ gitlab_version }}/{{ doc_path }}{{ file_name }}"
                ),
            }
        )

        doc_context = dict(default_provider_urls)
        doc_context.update(context)
        doc_context.update(doc_path=doc_path, file_name=file_name)

        for attrs, url_template in edit_url_attrs.items():
            if all(doc_context.get(attr) not in [None, "None"] for attr in attrs):
                return jinja2.Template(url_template).render(**doc_context)

        raise ExtensionError(
            "Missing required value for `use_edit_page_button`. "
            "Ensure one set of the following in your `html_context` "
            f"configuration: {sorted(edit_url_attrs.keys())}"
        )

    context["get_edit_url"] = get_edit_url

    # Ensure that the max TOC level is an integer
    context["theme_show_toc_level"] = int(context.get("theme_show_toc_level", 1))


# -----------------------------------------------------------------------------


def get_html_theme_path():
    """Return list of HTML theme paths."""
    theme_path = os.path.abspath(os.path.dirname(__file__))
    return [theme_path]


def setup(app):
    theme_path = get_html_theme_path()[0]
    app.add_html_theme("pydata_sphinx_theme", theme_path)
    app.set_translator("html", BootstrapHTML5Translator)

    # Read the Docs uses ``readthedocs`` as the name of the build, and also
    # uses a special "dirhtml" builder so we need to replace these both with
    # our custom HTML builder
    app.set_translator("readthedocs", BootstrapHTML5Translator, override=True)
    app.set_translator("readthedocsdirhtml", BootstrapHTML5Translator, override=True)
    app.connect("env-updated", update_config)
    app.connect("html-page-context", setup_edit_url)
    app.connect("html-page-context", add_toctree_functions)
    app.connect("html-page-context", update_templates)

    # Update templates for sidebar
    pkgdir = os.path.abspath(os.path.dirname(__file__))
    path_templates = os.path.join(pkgdir, "_templates")
    app.config.templates_path.append(path_templates)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
