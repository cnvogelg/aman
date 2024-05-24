import os
import time
import json
import logging

JSON_VERSION = 1
VERSION_TAG = "index_version"


class IndexLoc:
    def __init__(self, cache_id, page_num):
        self.cache_id = cache_id
        self.page_num = page_num

    def __repr__(self):
        return f"IndexLoc({self.cache_id, self.page_num})"

    def get_cache_id(self):
        return self.cache_id

    def get_page_num(self):
        return self.page_num

    def to_json(self):
        return [self.cache_id, self.page_num]

    @staticmethod
    def from_json(data):
        return IndexLoc(data[0], data[1])


class IndexEntry:
    def __init__(self):
        self.locs = []

    def __repr__(self):
        return f"IndexEntry({self.locs})"

    def add(self, loc):
        self.locs.append(loc)

    def get_locs(self):
        return self.locs

    def to_json(self):
        return list(map(lambda x: x.to_json(), self.locs))

    @staticmethod
    def from_json(data):
        entry = IndexEntry()
        for loc_data in data:
            loc = IndexLoc.from_json(loc_data)
            entry.add(loc)
        return entry


class PageIndex:
    def __init__(self, index_id, index_file, key_func):
        self.index_id = index_id
        self.index_file = index_file
        self.key_func = key_func
        self.index = None

    def setup(self, docs, force):
        ok = False
        if not force and os.path.exists(self.index_file):
            ok = self._load_index()
        if not ok:
            self._rebuild_index(docs)
            self._save_index()
        # return entries
        return len(self.index)

    def search(self, key):
        return self.index.get(key)

    def _load_index(self):
        start = time.monotonic()

        with open(self.index_file) as fh:
            data = json.load(fh)
        # check version
        if VERSION_TAG not in data:
            return False
        if data[VERSION_TAG] != JSON_VERSION:
            return False
        index = data["index"]
        self.index = {}
        for key, entry_data in index.items():
            entry = IndexEntry.from_json(entry_data)
            self.index[key] = entry

        end = time.monotonic()
        logging.info("loaded index '%s' in %.6f", self.index_id, end - start)
        return True

    def _save_index(self):
        start = time.monotonic()

        index = {}
        for key, entry in self.index.items():
            index[key] = entry.to_json()
        data = {VERSION_TAG: JSON_VERSION, "index": index}

        with open(self.index_file, "w") as fh:
            json.dump(data, fh)

        end = time.monotonic()
        logging.info("saved index '%s' in %.6f", self.index_id, end - start)

    def _rebuild_index(self, docs):
        start = time.monotonic()

        self.index = {}
        num_pages = 0
        for doc in docs:
            book = doc.get_book()
            page_num = 0
            for page in book.get_pages().values():
                # build index entry: cache file base name + page num in cache
                cache_id = doc.get_cache_id()
                loc = IndexLoc(cache_id, page_num)
                # generate key via key_func from page
                key = self.key_func(page)
                # new key?
                entry = self.index.get(key)
                if not entry:
                    entry = IndexEntry()
                    self.index[key] = entry
                entry.add(loc)
                page_num += 1

        end = time.monotonic()
        logging.info(
            "rebuild index '%s' with %s pages in %.6f",
            self.index_id,
            page_num,
            end - start,
        )


class PageIndices:
    def __init__(self):
        self.indices = []

    def add_index(self, index):
        self.indices.append(index)

    def add_long_title_index(self, index_dir):
        def key_long_title(page):
            return page.get_title()

        index_file = os.path.join(index_dir, "_long_title_index.json")
        index = PageIndex("long_title", index_file, key_long_title)
        self.add_index(index)
        return index

    def add_short_title_index(self, index_dir):
        def key_short_title(page):
            title = page.get_title()
            _, short = title.split("/")
            return short

        index_file = os.path.join(index_dir, "_short_title_index.json")
        index = PageIndex("short_title", index_file, key_short_title)
        self.add_index(index)
        return index

    def setup(self, doc_set, force):
        num_entries = 0
        num_indices = 0
        docs = doc_set.get_docs()
        start = time.monotonic()

        for index in self.indices:
            num_entries += index.setup(docs, force)
            num_indices += 1

        end = time.monotonic()
        logging.info(
            "setup %d indices with %s entries in %.6f (forced=%s)",
            num_indices,
            num_entries,
            end - start,
            force,
        )

    def search(self, key):
        for index in self.indices:
            entry = index.search(key)
            if entry:
                return entry
