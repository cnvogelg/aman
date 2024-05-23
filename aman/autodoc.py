import logging
import time
import json

from .parse import parse_autodoc
from .scan import scan_autodocs, scan_cache
from .book import AutoDocBook

VERSION_TAG = "autobook_version"
JSON_VERSION = 1


class AutoDoc:
    def __init__(self, name, doc_path, doc_mtime):
        self.name = name
        self.doc_path = doc_path
        self.doc_mtime = doc_mtime
        self.cache_path = None
        self.cache_mtime = 0
        self.book = None

    def set_cache_file(self, cache_path, cache_mtime):
        self.cache_path = cache_path
        self.cache_mtime = cache_mtime

    def get_name(self):
        return self.name

    def get_doc_path(self):
        return self.doc_path

    def is_cache_valid(self):
        return self.cache_mtime > self.doc_mtime

    def get_book(self):
        return self.book

    def __repr__(self):
        return f"AutoDoc({self.doc_path}, {self.name}, {self.mtime})"

    def setup_cache(self, force=False):
        # check if cache is valid otherwise reload
        if not self.is_cache_valid() or force:
            self._build_cache()
        # load cache - if it fails rebuild
        elif not self._load_cache():
            self._build_cache()
        # return pages
        return self.book.get_num_pages()

    def _build_cache(self):
        logging.info("parsing autodoc from '%s'", self.doc_path)
        start = time.monotonic()
        self.book = parse_autodoc(self.doc_path)
        end = time.monotonic()
        num = len(self.book.get_toc())
        logging.info("found %s entries in %.6f", num, end - start)
        self._save_cache()

    def _save_cache(self):
        data = {VERSION_TAG: JSON_VERSION, "book": self.book.to_json()}
        with open(self.cache_path, "w") as fh:
            json.dump(data, fh)

    def _load_cache(self):
        start = time.monotonic()
        with open(self.cache_path) as fh:
            data = json.load(fh)
        # check version
        if VERSION_TAG not in data:
            return False
        if data[VERSION_TAG] != JSON_VERSION:
            return False
        # read data
        self.book = AutoDocBook(self.doc_path)
        ok = self.book.from_json(data["book"])
        end = time.monotonic()
        logging.info(
            "load cache from '%s' in %.6f ok=%s", self.cache_path, end - start, ok
        )
        return ok


class AutoDocSet:
    def __init__(self):
        self.docs = []

    def add_doc(self, doc):
        self.doc.append(doc)

    def setup(self, doc_paths, cache_dir, force_rebuild):
        start = time.monotonic()

        # scan for autodocs
        for path in doc_paths:
            self.docs += scan_autodocs(path, AutoDoc)

        # scan the cache
        scan_cache(cache_dir, self.docs)

        # setup cache
        total_pages = 0
        for doc in self.docs:
            pages = doc.setup_cache(force_rebuild)
            total_pages += pages

        end = time.monotonic()
        num_books = len(self.docs)
        logging.info(
            "loaded doc set with %s books (%s pages) in %.6f",
            num_books,
            total_pages,
            end - start,
        )
