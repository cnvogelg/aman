class AutoDocBook:
    def __init__(self, file_name):
        self.file_name = file_name
        self.toc = []
        self.topics = []
        self.pages = {}

    def __repr__(self):
        return f"AutoDocBook({self.file_name},#toc={len(self.toc)})"

    def add_page(self, title, page):
        self.toc.append(title)
        self.pages[title] = page

    def add_topic(self, topic):
        self.topics.append(topic)

    def get_toc(self):
        return self.toc

    def get_topics(self):
        return self.topics

    def get_num_pages(self):
        return len(self.toc)

    def get_page(self, title):
        return self.pages[title]

    def get_pages(self):
        return self.pages

    def to_json(self):
        pages = {}
        for name, page in self.pages.items():
            pages[name] = page.to_json()
        return {"toc": self.toc, "pages": pages, "topics": self.topics}

    def from_json(self, data):
        if "toc" not in data:
            return False
        if "pages" not in data:
            return False
        self.toc = data["toc"]
        self.topics = data["topics"]
        self.pages = {}
        page_data = data["pages"]
        for title in self.toc:
            page = AutoDocPage(title)
            page.set_book(self)
            ok = page.from_json(page_data[title])
            if not ok:
                return False
            self.pages[title] = page
        return True


class AutoDocPage:
    def __init__(self, title):
        self.title = title
        self.raw_page = None
        self.toc = []
        self.sections = {}
        self.book = None

    def __repr__(self):
        return f"AutoDocPage({self.title},#toc={len(self.toc)})"

    def format_txt_lines(self):
        lines = []
        lines.append(self.title)
        lines.append("")
        for section in self.toc:
            lines.append(section)
            for line in self.sections[section]:
                lines.append("\t" + line)
            lines.append("")
        return lines

    def dump_raw(self, p=print):
        p(self.title)
        p(self.raw_page)

    def add_section(self, title, lines):
        self.toc.append(title)
        self.sections[title] = lines

    def set_book(self, book):
        self.book = book

    def get_book(self):
        return self.book

    def set_raw_page(self, raw_page):
        self.raw_page = raw_page

    def get_title(self):
        return self.title

    def get_raw_page(self):
        return self.raw_page

    def get_toc(self):
        return self.toc

    def get_section(self, title):
        return self.sections[title]

    def find_section(self, title):
        return self.sections.get(title)

    def get_sections(self):
        return self.sections

    def to_json(self):
        return {"toc": self.toc, "sections": self.sections, "raw_page": self.raw_page}

    def from_json(self, data):
        if "toc" not in data:
            return False
        if "sections" not in data:
            return False
        if "raw_page" not in data:
            return False
        self.toc = data["toc"]
        self.raw_page = data["raw_page"]
        self.sections = {}
        sections_data = data["sections"]
        for title in self.toc:
            self.sections[title] = sections_data[title]
        return True
