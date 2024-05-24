"""aman - read Amiga autodocs as man pages"""

import argparse
import os
import sys
import logging

from .autodoc import AutoDocSet
from .index import PageIndices

LOGGING_FORMAT = "%(message)s"
AMAN_PATH_VAR = "AMANPATH"
AMAN_CACHE_VAR = "AMANCACHE"
AMAN_DEFAULT_CACHE_DIR = "~/.aman/cache"
DESC = "read Amiga autodocs as man pages"


def aman(man_paths, cache_dir, keyword, force_rebuild=False, raw_page=False):
    logging.info(
        "man_paths=%s, cache_dir=%s, keyword=%s", man_paths, cache_dir, keyword
    )

    # ensure cache dir
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    # setup doc set
    doc_set = AutoDocSet()
    is_clean = doc_set.setup(
        man_paths, cache_dir, force_rebuild=force_rebuild, zip_cache=True
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
            loc = locs[0]
            book, page = doc_set.resolve_book_page(loc)
            if raw_page:
                page.dump_raw()
            else:
                page.dump()
        else:
            # multiple matches -> list matches
            for loc in locs:
                book, page = doc_set.resolve_book_page(loc)
                print(page.get_title())

    return 0


def main():
    # parse args
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument(
        "-M", "--man-path", help="Define the paths of the Amiga autodocs"
    )
    parser.add_argument("-c", "--cache-dir", help="directory for cache files")
    parser.add_argument("-r", "--raw-page", action="store_true", help="show raw page")
    parser.add_argument(
        "-f", "--force", action="store_true", help="force recreation of cache"
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

    # get man path
    if opts.man_path:
        man_path = opts.man_path
    elif AMAN_PATH_VAR in os.environ:
        man_path = os.environ[AMAN_PATH_VAR]
    else:
        logging.error(
            "No path for autodocs given. Set env var %s or use -M option", AMAN_PATH_VAR
        )
        sys.exit(1)
    # split multiple paths
    man_paths = man_path.split(os.pathsep)

    # get cache dir
    if opts.cache_dir:
        cache_dir = opts.cache_dir
    elif AMAN_CACHE_VAR in os.environ:
        cache_dir = os.environ[AMAN_PATH_VAR]
    else:
        cache_dir = os.path.expanduser(AMAN_DEFAULT_CACHE_DIR)

    # call main
    result = aman(
        man_paths,
        cache_dir,
        opts.keyword,
        force_rebuild=opts.force,
        raw_page=opts.raw_page,
    )
    sys.exit(result)
