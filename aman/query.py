import logging

from .index import PageIndices


class Query:
    # with index
    QUERY_MODE_PAGE = 0
    QUERY_MODE_TOPIC_PAGE = 1
    QUERY_MODE_SEE_ALSO = 2

    # without index
    QUERY_MODE_SYNOPSIS = 3
    QUERY_MODE_FULL_TEXT = 4

    def __init__(self):
        self.mode = self.QUERY_MODE_PAGE
        self.indices = PageIndices()
        self.search_func = self._search_index
        self.limit_books = None
        self.ignore_case = False

    def set_mode(self, mode):
        self.mode = mode

    def set_limit_books(self, books):
        self.limit_books = books

    def set_ignore_case(self, ignore_case):
        self.ignore_case = ignore_case

    def _search_index(self, keyword):
        entry = self.indices.search(keyword)
        if entry:
            return entry.get_page_refs()
        else:
            return None

    def setup(self, doc_set, cache_dir, force_rebuild, zip_index):
        logging.info("query ignore case: %s", self.ignore_case)
        if self.mode == self.QUERY_MODE_PAGE:
            logging.info("query mode: page")
            self.indices.add_title_index(self.ignore_case)
        elif self.mode == self.QUERY_MODE_TOPIC_PAGE:
            logging.info("query mode: topic_page")
            self.indices.add_topic_title_index(self.ignore_case)
        elif self.mode == self.QUERY_MODE_SEE_ALSO:
            logging.info("query mode: see_also")
            self.indices.add_see_also_index(self.ignore_case)

        # setup index if any
        if self.indices:
            self.indices.setup(doc_set, cache_dir, force_rebuild, zip_index)

    def search(self, keyword):
        """search for keyword and return one or more page_refs"""
        page_refs = self.search_func(keyword)
        if not self.limit_books:
            return page_refs
        else:
            return list(
                filter(lambda x: x.get_doc_name() in self.limit_books, page_refs)
            )
