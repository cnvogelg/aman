from .index import PageIndices


class Query:
    # with index
    QUERY_MODE_PAGE = 0
    QUERY_MODE_BOOK_PAGE = 1
    QUERY_MODE_SEE_ALSO = 2

    # without index
    QUERY_MODE_SYNOPSIS = 3
    QUERY_MODE_FULL_TEXT = 4

    def __init__(self):
        self.mode = self.QUERY_MODE_PAGE
        self.indices = PageIndices()
        self.search_func = self._search_index

    def set_mode(self, mode):
        self.mode = mode

    def _search_index(self, keyword):
        entry = self.indices.search(keyword)
        if entry:
            return entry.get_page_refs()
        else:
            return None

    def setup(self, doc_set, cache_dir, force_rebuild, zip_index):
        if self.mode == self.QUERY_MODE_PAGE:
            self.indices.add_short_title_index()
        elif self.mode == self.QUERY_MODE_BOOK_PAGE:
            self.indices.add_long_title_index()

        # setup index if any
        if self.indices:
            self.indices.setup(doc_set, cache_dir, force_rebuild, zip_index)

    def search(self, keyword):
        """search for keyword and return one or more page_refs"""
        return self.search_func(keyword)
