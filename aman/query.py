import logging
import time

from .index import PageIndices, IndexPageRef


class Query:
    # with index
    QUERY_MODE_PAGE = 0
    QUERY_MODE_TOPIC_PAGE = 1
    QUERY_MODE_SEE_ALSO = 2

    # without index
    QUERY_MODE_FULL_SECTION = 3
    QUERY_MODE_FULL_PAGE = 4

    def __init__(self):
        self.mode = self.QUERY_MODE_PAGE
        self.indices = PageIndices()
        self.search_func = self._search_index
        self.limit_books = None
        self.ignore_case = False
        self.section = None

    def set_mode(self, mode):
        self.mode = mode

    def set_limit_books(self, books):
        self.limit_books = books

    def set_ignore_case(self, ignore_case):
        self.ignore_case = ignore_case

    def set_section(self, section):
        self.section = section

    def _search_index(self, keyword):
        entry = self.indices.search(keyword)
        if entry:
            return entry.get_page_refs()
        else:
            return None

    def _full_search(self, doc_set, keyword, page_search_func):
        page_refs = []
        # brute force search through all docs
        for doc in sorted(doc_set.get_docs(), key=lambda x: x.get_name()):
            # skip books?
            if self.limit_books:
                if doc.get_name() in self.limit_books:
                    logging.info("full search: skip book %s", book)
                    continue
            # load book
            book = doc.get_book()
            logging.info("full search: book %s", book)
            # run through pages
            for page in book.get_pages().values():
                # call page search func
                found = page_search_func(page, keyword)
                logging.info("full search: page %s -> %s", page, found)
                if found:
                    page_ref = IndexPageRef(doc.get_name(), page.get_title())
                    page_refs.append(page_ref)
        return page_refs

    def _section_page_search(self, page, keyword):
        logging.info("page=%s", page)
        # no section given
        if not self.section:
            return False
        # find section in page
        section = page.find_section(self.section)
        if not section:
            logging.debug(
                "section search: '%s' not in %s",
                self.section,
            )
            return False
        # scan through section
        for line in section:
            if self.ignore_case:
                line = line.lower()
            if line.find(keyword) != -1:
                return True

    def _full_page_search(self, page, keyword):
        for section in page.get_sections().values():
            for line in section:
                if self.ignore_case:
                    line = line.lower()
                if line.find(keyword) != -1:
                    return True

    def setup(self, doc_set, cache_dir, force_rebuild, zip_index):
        logging.info("query ignore case: %s", self.ignore_case)
        # search page by title
        if self.mode == self.QUERY_MODE_PAGE:
            logging.info("query mode: page")
            self.indices.add_title_index(self.ignore_case)
        # search page by topic/title
        elif self.mode == self.QUERY_MODE_TOPIC_PAGE:
            logging.info("query mode: topic_page")
            self.indices.add_topic_title_index(self.ignore_case)
        # search in SEE ALSO section
        elif self.mode == self.QUERY_MODE_SEE_ALSO:
            logging.info("query mode: see_also")
            self.indices.add_see_also_index(self.ignore_case)
        # non-index searches: search a section
        elif self.mode == self.QUERY_MODE_FULL_SECTION:

            def search(keyword):
                return self._full_search(doc_set, keyword, self._section_page_search)

            self.search_func = search
            self.indices = None
        # non-index searches: search full page
        elif self.mode == self.QUERY_MODE_FULL_PAGE:

            def search(keyword):
                return self._full_search(doc_set, keyword, self._full_page_search)

            self.search_func = search
            self.indices = None

        # setup index if any
        if self.indices:
            self.indices.setup(doc_set, cache_dir, force_rebuild, zip_index)

    def search(self, keyword):
        """search for keyword and return one or more page_refs"""
        if self.ignore_case:
            keyword = keyword.lower()

        start = time.monotonic()
        page_refs = self.search_func(keyword)
        end = time.monotonic()
        logging.info("search for '%s' took %0.6f", keyword, end - start)

        # limit result to books?
        if not self.limit_books:
            return page_refs
        else:
            return list(
                filter(lambda x: x.get_doc_name() in self.limit_books, page_refs)
            )
