"""aman - read Amiga autodocs as man pages"""

import argparse
import os
import sys
import logging

from .autodoc import AutoDocSet
from .index import PageIndices
from .config import Config
from .format import Format

LOGGING_FORMAT = "%(message)s"
AMAN_DEFAULT_CONFIG_FILE = "~/.aman/config.json"
DESC = "read Amiga autodocs as man pages"


def aman(config, keyword, fmt, force_rebuild=False, all_pages=False):
    cache_dir = config.get_cache_dir()

    # setup doc set
    doc_set = AutoDocSet()
    is_clean = doc_set.setup(
        config.get_man_paths(), cache_dir, force_rebuild=force_rebuild, zip_cache=True
    )

    # setup search indices
    indices = PageIndices()
    short_index = indices.add_short_title_index()
    long_index = indices.add_long_title_index()
    force = not is_clean
    indices.setup(doc_set, cache_dir, force_rebuild=force, zip_index=True)

    # search key
    entry = indices.search(keyword)
    if not entry:
        # no entry
        print(f"no entry found for '{keyword}'")
    else:
        # get locations
        locs = entry.get_locs()
        if len(locs) == 1:
            # single match -> show page
            page = doc_set.resolve_page(locs[0])
            fmt.format_page(page)
        else:
            # multiple matches -> list matches
            pages = doc_set.resolve_pages(locs)
            if all_pages:
                # show pages one by one
                for page in pages:
                    fmt.format_page(page)
            else:
                # show page list
                fmt.format_page_list(pages)

    return 0


def main():
    # parse args
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument(
        "-M", "--man-path", help="Define the paths of the Amiga autodocs"
    )
    parser.add_argument("-C", "--cache-dir", help="directory for cache files")
    parser.add_argument("-c", "--config-file", help="config file")
    parser.add_argument(
        "-f", "--force", action="store_true", help="force recreation of cache"
    )
    parser.add_argument("-n", "--no-pager", action="store_true", help="disable pager")
    parser.add_argument("-P", "--pager", help="pager executable")
    parser.add_argument("-j", "--json", action="store_true", help="output json format")
    parser.add_argument("-r", "--raw-page", action="store_true", help="show raw page")
    parser.add_argument(
        "-a", "--all-pages", action="store_true", help="show multiple results as pages"
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="be more verbose", default=0
    )
    parser.add_argument("keyword", help="keyword to search for")
    opts = parser.parse_args()

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

    # call main
    result = aman(
        config, opts.keyword, fmt, force_rebuild=opts.force, all_pages=opts.all_pages
    )
    sys.exit(result)
