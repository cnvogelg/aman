"""aman - read Amiga autodocs as man pages"""

import argparse
import os
import sys
import logging

from .autodoc import AutoDocSet

LOGGING_FORMAT = "%(message)s"
AMAN_PATH_VAR = "AMANPATH"
AMAN_CACHE_VAR = "AMANCACHE"
AMAN_DEFAULT_CACHE_DIR = "~/.aman/cache"
DESC = "read Amiga autodocs as man pages"


def aman(man_paths, cache_dir, keyword, force_rebuild):
    logging.info(
        "man_paths=%s, cache_dir=%s, keyword=%s", man_paths, cache_dir, keyword
    )

    # ensure cache dir
    if not os.path.isdir(cache_dir):
        os.makedirs(cache_dir)

    # setup doc set
    doc_set = AutoDocSet()
    doc_set.setup(man_paths, cache_dir, force_rebuild)

    return 0


def main():
    # parse args
    parser = argparse.ArgumentParser(description=DESC)
    parser.add_argument(
        "-M", "--man-path", help="Define the paths of the Amiga autodocs"
    )
    parser.add_argument("-c", "--cache-dir", help="directory for cache files")
    parser.add_argument(
        "-f", "--force", action="store_true", help="force recreation of cache"
    )
    parser.add_argument(
        "-d", "--debug", action="store_true", help="enabled debug output"
    )
    parser.add_argument("keyword", help="keyword to search for")
    opts = parser.parse_args()

    # setup logging
    if opts.debug:
        level = logging.DEBUG
    else:
        level = logging.WARNING
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
    result = aman(man_paths, cache_dir, opts.keyword, opts.force)
    sys.exit(result)
