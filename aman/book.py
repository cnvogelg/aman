class AutoDocBook:
    def __init__(self, file_name):
        self.file_name = file_name
        self.toc = []
        self.pages = {}

    def __repr__(self):
        return f"AutoDocBook({self.file_name},#toc={len(self.toc)})"

    def add_page(self, title, page):
        self.toc.append(title)
        self.pages[title] = page

    def get_toc(self):
        return self.toc

    def get_num_pages(self):
        return len(self.toc)

    def get_page(self, title):
        return self.pages[title]

    def get_page_at(self, page_num):
        return self.pages[self.toc[page_num]]

    def get_pages(self):
        return self.pages

    def to_json(self):
        pages = {}
        for name, page in self.pages.items():
            pages[name] = page.to_json()
        return {"toc": self.toc, "pages": pages}

    def from_json(self, data):
        if "toc" not in data:
            return False
        if "pages" not in data:
            return False
        self.toc = data["toc"]
        self.pages = {}
        page_data = data["pages"]
        for title in self.toc:
            page = AutoDocPage(title)
            ok = page.from_json(page_data[title])
            if not ok:
                return False
            self.pages[title] = page
        return True


class AutoDocPage:
    def __init__(self, title):
        self.title = title
        self.toc = []
        self.sections = {}

    def __repr__(self):
        return f"AutoDocPage({self.title},#toc={len(self.toc)})"

    def dump(self, p=print):
        p(self.title)
        p()
        for section in self.toc:
            p(section)
            for line in self.sections[section]:
                p("\t" + line)

    def add_section(self, title, lines):
        self.toc.append(title)
        self.sections[title] = lines

    def get_title(self):
        return self.title

    def get_toc(self):
        return self.toc

    def get_section(self, title):
        return self.sections[title]

    def get_sections(self):
        return self.sections

    def to_json(self):
        return {"toc": self.toc, "sections": self.sections}

    def from_json(self, data):
        if "toc" not in data:
            return False
        if "sections" not in data:
            return False
        self.toc = data["toc"]
        self.sections = {}
        sections_data = data["sections"]
        for title in self.toc:
            self.sections[title] = sections_data[title]
        return True
