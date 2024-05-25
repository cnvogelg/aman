"""aman - read Amiga autodocs as man pages"""

import argparse
import os
import sys
import logging

from .autodoc import AutoDocSet
from .config import Config, ENV_DESC
from .format import Format
from .query import Query

LOGGING_FORMAT = "%(message)s"
AMAN_DEFAULT_CONFIG_FILE = "~/.aman/config.json"
DESC = "read Amiga autodocs as man pages"


def aman(
    config,
    keywords,
    query,
    fmt,
    force_rebuild=False,
    all_pages=False,
    list_books=False,
    list_pages=None,
):
    cache_dir = config.get_cache_dir()

    # setup doc set
    doc_set = AutoDocSet()
    is_clean = doc_set.setup(
        config.get_man_paths(), cache_dir, force_rebuild=force_rebuild, zip_cache=True
    )

    # list only books
    if list_books:
        docs = doc_set.get_docs()
        titles = map(lambda x: x.get_name(), docs)
        for title in sorted(titles):
            print(title)
        return 0

    # list only pages
    if list_pages:
        doc = doc_set.find_doc(list_pages)
        if doc:
            book = doc.get_book()
            for title in book.get_toc():
                print(title)
            return 0
        else:
            print(f"doc book '{list_pages}' not found!")
            return 1

    # now at least one keyword is required
    if len(keywords) == 0:
        print("no search keyword given!")
        return 2

    # setup query
    force_rebuild = not is_clean
    query.setup(doc_set, cache_dir, force_rebuild, zip_index=True)

    # perform search for each keyword
    for key in keywords:
        page_refs = query.search(key)
        if not page_refs:
            # no entry
            print(f"no entry found for '{key}'")
        elif len(page_refs) == 1:
            # single match -> show page
            page = doc_set.resolve_page_ref(page_refs[0])
            fmt.format_page(page)
        else:
            # multiple matches -> list matches
            pages = doc_set.resolve_page_refs(page_refs)
            if all_pages:
                # show pages one by one
                for page in pages:
                    fmt.format_page(page)
            else:
                # show page list
                fmt.format_page_list(pages)

    return 0


def parse_args():
    # parse args
    parser = argparse.ArgumentParser(
        description=DESC,
        epilog=ENV_DESC,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="be more verbose", default=0
    )

    # mode args
    mode_grp = parser.add_argument_group("mode options")
    mode_grp.add_argument(
        "-b", "--list-books", action="store_true", help="show available books and quit"
    )
    mode_grp.add_argument(
        "-p",
        "--list-pages",
        nargs="?",
        help="show available pages of a given book and quit",
    )

    # search
    search_grp = parser.add_argument_group("search options")
    search_grp.add_argument("keywords", nargs="*", help="keywords to search for")

    # output args
    output_grp = parser.add_argument_group("output options")
    output_grp.add_argument(
        "-n", "--no-pager", action="store_true", help="disable pager"
    )
    output_grp.add_argument(
        "-j", "--json", action="store_true", help="output in json format"
    )
    output_grp.add_argument(
        "-r",
        "--raw-page",
        action="store_true",
        help="show raw page of autodoc otherwise reformat and colorize",
    )
    output_grp.add_argument(
        "-a",
        "--all-pages",
        action="store_true",
        help="show multiple results as pages and no list",
    )
    output_grp.add_argument("--color", action="store_true", help="use colorful output")
    output_grp.add_argument(
        "--no-color", action="store_true", help="disable colorful output"
    )

    # config args
    config_grp = parser.add_argument_group("config options")
    config_grp.add_argument(
        "-M", "--man-path", help="Define the paths of the Amiga autodocs"
    )
    config_grp.add_argument("-C", "--cache-dir", help="directory for cache files")
    config_grp.add_argument("-c", "--config-file", help="config file")
    config_grp.add_argument(
        "-f", "--force", action="store_true", help="force recreation of cache"
    )
    config_grp.add_argument("-P", "--pager", help="pager command line")

    return parser.parse_args()


def main():
    opts = parse_args()

    # setup logging
    if opts.verbose == 0:
        level = logging.WARNING
    elif opts.verbose == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logging.basicConfig(format=LOGGING_FORMAT, level=level)

    # locate config file
    if opts.config_file:
        config_file = opts.config_file
    else:
        config_file = os.path.expanduser(AMAN_DEFAULT_CONFIG_FILE)

    # setu config from file and env
    config = Config(config_file=config_file, use_env=True)

    # apply options from command line
    if opts.man_path:
        man_paths = opts.man_path.split(os.pathsep)
        config.set_man_paths(man_paths)
        man_path = opts.man_path

    # cache dir
    if opts.cache_dir:
        config.set_cache_dir(opts.cache_dir)

    # pager setting
    if opts.no_pager:
        config.set_pager(None)
    elif opts.pager:
        config.set_pager(opts.pager)

    # check config
    if not config.finalize():
        sys.exit(1)

    # setup format
    fmt = Format()
    fmt.set_pager(config.get_pager())
    if opts.raw_page:
        fmt.set_output_format(Format.OUTPUT_FORMAT_RAW)
    elif opts.json:
        fmt.set_output_format(Format.OUTPUT_FORMAT_JSON)
    # colorize?
    if opts.color:
        fmt.set_color(True)
    elif opts.no_color:
        fmt.set_color(False)
    else:
        # check terminal
        colorize = sys.stdout.isatty()
        fmt.set_color(colorize)

    # setup query
    query = Query()

    # call main
    result = aman(
        config,
        opts.keywords,
        query,
        fmt,
        force_rebuild=opts.force,
        all_pages=opts.all_pages,
        list_books=opts.list_books,
        list_pages=opts.list_pages,
    )
    sys.exit(result)
