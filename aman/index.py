import os
import re
import time
import json
import logging
import gzip

JSON_VERSION = 1
VERSION_TAG = "index_version"


class IndexPageRef:
    def __init__(self, doc_name, page_title):
        self.doc_name = doc_name
        self.page_title = page_title

    def __repr__(self):
        return f"IndexPageRef({self.doc_name, self.page_title})"

    def get_doc_name(self):
        return self.doc_name

    def get_page_title(self):
        return self.page_title

    def to_json(self):
        return {"doc_name": self.doc_name, "page_title": self.page_title}

    @staticmethod
    def from_json(data):
        doc_name = data["doc_name"]
        page_title = data["page_title"]
        return IndexPageRef(doc_name, page_title)


class IndexEntry:
    def __init__(self):
        self.page_refs = []

    def __repr__(self):
        return f"IndexEntry({self.page_refs})"

    def add_page_ref(self, page_ref):
        self.page_refs.append(page_ref)

    def get_page_refs(self):
        return self.page_refs

    def to_json(self):
        return list(map(lambda x: x.to_json(), self.page_refs))

    @staticmethod
    def from_json(data):
        entry = IndexEntry()
        for page_ref_data in data:
            page_ref = IndexPageRef.from_json(page_ref_data)
            entry.add_page_ref(page_ref)
        return entry


class PageIndex:
    def __init__(self, index_id, keys_func, ignore_case=False):
        self.index_id = index_id
        self.keys_func = keys_func
        self.ignore_case = ignore_case
        self.index = None
        self.index_file = None
        self.index_zip = False

    def setup(self, docs, index_dir, force_rebuild=False, zip_index=False):
        # set cache file name
        index_name = "_index_" + self.index_id
        if self.ignore_case:
            index_name += "_ic"
        index_name += ".json"
        if zip_index:
            index_name += ".gz"
        index_file = os.path.join(index_dir, index_name)
        self.index_file = index_file
        self.index_zip = zip_index
        # load or rebuild+save index
        ok = False
        if not force_rebuild and os.path.exists(self.index_file):
            ok = self._load_index()
        if not ok:
            self._rebuild_index(docs)
            self._save_index()
        # return entries
        return len(self.index)

    def search(self, key):
        if self.ignore_case:
            key = key.lower()
        return self.index.get(key)

    def _load_index(self):
        start = time.monotonic()

        # load index file
        if self.index_zip:
            with gzip.open(self.index_file, "rt") as fh:
                data = json.load(fh)
        else:
            with open(self.index_file) as fh:
                data = json.load(fh)

        # check version
        if VERSION_TAG not in data:
            return False
        if data[VERSION_TAG] != JSON_VERSION:
            return False

        # load entries
        index = data["index"]
        self.index = {}
        for key, entry_data in index.items():
            entry = IndexEntry.from_json(entry_data)
            self.index[key] = entry

        end = time.monotonic()
        logging.info("loaded index '%s' in %.6f", self.index_file, end - start)
        return True

    def _save_index(self):
        start = time.monotonic()

        # store entries and version
        index = {}
        for key, entry in self.index.items():
            index[key] = entry.to_json()
        data = {VERSION_TAG: JSON_VERSION, "index": index}

        # save index file
        if self.index_zip:
            with gzip.open(self.index_file, "wt") as fh:
                json.dump(data, fh)
        else:
            with open(self.index_file, "w") as fh:
                json.dump(data, fh)

        end = time.monotonic()
        logging.info("saved index '%s' in %.6f", self.index_file, end - start)

    def _rebuild_index(self, docs):
        start = time.monotonic()

        self.index = {}
        num_keys = 0
        num_pages = 0
        # iterate over all books and its pages
        for doc in docs:
            book = doc.get_book()
            for page in book.get_pages().values():
                # build page_ref: doc_name + page title
                doc_name = doc.get_name()
                page_title = page.get_title()
                page_ref = IndexPageRef(doc_name, page_title)

                # generate keys via key_func from page
                keys = self.keys_func(page)

                # add keys
                if keys:
                    for key in keys:
                        # ignore case -> lowercase
                        if self.ignore_case:
                            key = key.lower()
                        # new key?
                        entry = self.index.get(key)
                        if not entry:
                            entry = IndexEntry()
                            self.index[key] = entry
                        entry.add_page_ref(page_ref)
                        num_keys += 1
                    num_pages += 1

        end = time.monotonic()
        logging.info(
            "rebuild index '%s' with %s pages and %s keys in %.6f",
            self.index_id,
            num_pages,
            num_keys,
            end - start,
        )


class PageIndices:
    def __init__(self):
        self.indices = []

    def add_index(self, index):
        self.indices.append(index)

    def add_topic_title_index(self, ignore_case=True):
        def key_func(page):
            return [page.get_title()]

        index = PageIndex("topic_title", key_func, ignore_case=ignore_case)
        self.add_index(index)
        return index

    def add_title_index(self, ignore_case=True):
        def key_func(page):
            title = page.get_title()
            _, short = title.split("/")
            return [short]

        index = PageIndex("title", key_func, ignore_case=ignore_case)
        self.add_index(index)
        return index

    def _sanitize_entry(self, entry):
        e = entry.strip()
        e = e.replace("()", "")  # remove functions
        e = e.replace("(2)", "")  # some bsdsocket functions use this
        return e

    def add_see_also_index(self, ignore_case=True):
        def key_func(page):
            see_also = page.find_section("SEE ALSO")
            if see_also:
                data = ", ".join(see_also)
                entries = data.split(",")
                keys = []
                for entry in entries:
                    e = self._sanitize_entry(entry)
                    if e:
                        keys.append(e)
                return keys

        index = PageIndex("see_also", key_func, ignore_case=ignore_case)
        self.add_index(index)
        return index

    def setup(self, doc_set, index_dir, force_rebuild=False, zip_index=False):
        num_entries = 0
        num_indices = 0
        docs = doc_set.get_docs()
        start = time.monotonic()

        for index in self.indices:
            num_entries += index.setup(
                docs, index_dir, force_rebuild=force_rebuild, zip_index=zip_index
            )
            num_indices += 1

        end = time.monotonic()
        logging.info(
            "setup %d indices with %s entries in %.6f (forced=%s)",
            num_indices,
            num_entries,
            end - start,
            force_rebuild,
        )

    def search(self, key):
        for index in self.indices:
            entry = index.search(key)
            if entry:
                return entry
