import os
import logging
import time
import json

from .parse import parse_autodoc
from .scan import scan_autodocs, scan_cache
from .book import AutoDocBook
from .index import PageIndex

VERSION_TAG = "autobook_version"
JSON_VERSION = 1


class AutoDoc:
    def __init__(self, name, doc_path, doc_mtime):
        self.name = name
        self.doc_path = doc_path
        self.doc_mtime = doc_mtime
        self.cache_path = None
        self.cache_mtime = 0
        self.cache_id = None
        self.book = None

    def set_cache_file(self, cache_path, cache_mtime):
        self.cache_path = cache_path
        self.cache_mtime = cache_mtime
        self.cache_id = os.path.basename(cache_path)

    def get_name(self):
        return self.name

    def get_doc_path(self):
        return self.doc_path

    def get_cache_path(self):
        return self.cache_path

    def get_cache_id(self):
        return self.cache_id

    def is_cache_valid(self):
        return self.cache_mtime > self.doc_mtime

    def get_book(self):
        # need to load cache?
        if not self.book:
            ok = self._load_cache()
            if not ok:
                logging.error("can't load cache '%s'", self.cache_path)
        return self.book

    def __repr__(self):
        return f"AutoDoc({self.doc_path}, {self.name}, {self.mtime})"

    def setup_cache(self, force=False):
        """load or build/save cache. return True if cache was valid"""
        # check if cache is valid otherwise reload
        if not self.is_cache_valid() or force:
            self._build_cache()
            return False
        else:
            return True

    def _build_cache(self):
        logging.info("parsing autodoc from '%s'", self.doc_path)
        start = time.monotonic()

        self.book = parse_autodoc(self.doc_path)
        end = time.monotonic()
        num = len(self.book.get_toc())
        self._save_cache()

        logging.info("stored %s entries in %.6f", num, end - start)

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
        self.index = None
        self.short_index = None
        self.cache_dir = None
        self.cache_doc_map = {}

    def add_doc(self, doc):
        self.doc.append(doc)

    def setup(self, doc_paths, cache_dir, force_rebuild):
        start = time.monotonic()

        # scan for autodocs
        for path in doc_paths:
            self.docs += scan_autodocs(path, AutoDoc)

        # scan the cache
        self.cache_dir = cache_dir
        scan_cache(cache_dir, self.docs)

        # setup cache
        all_valid = True
        for doc in self.docs:
            was_valid = doc.setup_cache(force_rebuild)
            all_valid = all_valid and was_valid
            # store mapping: cache_id -> doc
            self.cache_doc_map[doc.get_cache_id()] = doc

        end = time.monotonic()
        num_books = len(self.docs)
        logging.info(
            "setup doc set with %s books in %.6f (all valid=%s)",
            num_books,
            end - start,
            all_valid,
        )

        # prepare index
        def key_title(page):
            return page.get_title()

        def key_short_title(page):
            title = page.get_title()
            _, short = title.split("/")
            return short

        start = time.monotonic()
        force_index = not all_valid

        index_file = os.path.join(cache_dir, "_index.json")
        self.index = PageIndex(index_file, self.docs, key_title)
        num_entries = self.index.setup(force_index)

        short_index_file = os.path.join(cache_dir, "_short_index.json")
        self.short_index = PageIndex(short_index_file, self.docs, key_short_title)
        num_entries += self.short_index.setup(force_index)

        end = time.monotonic()
        logging.info(
            "setup index with %s entries in %.6f (forced=%s)",
            num_entries,
            end - start,
            force_index,
        )

        return all_valid

    def search(self, key):
        entry = self.short_index.search(key)
        if not entry:
            entry = self.index.search(key)
        return entry

    def resolve_book_page(self, loc):
        cache_id = loc.get_cache_id()
        doc = self.cache_doc_map[cache_id]
        book = doc.get_book()
        page = book.get_page_at(loc.get_page_num())
        return book, page
