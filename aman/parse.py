import logging

from .book import AutoDocBook, AutoDocPage


class ParseError(Exception):
    pass


def cleanup_line(line):
    return line.replace("\t", "    ")


def get_indent(line):
    n = len(line)
    if n == 0:
        return 0
    num = 0
    while line[num] == " ":
        num += 1
        if num == n:
            break
    return num


def get_section_header(line, indent):
    """check if line is a section heading"""
    # indent must be 3 or 4
    if indent not in (3, 4):
        return None
    # must be alpha or space
    heading = line[indent:]
    test = heading.replace(" ", "")
    if not test.isalpha():
        return None
    # must be upper case
    if heading != heading.upper():
        return None
    # ok, is a section header
    return heading


def remove_empty_sec_lines(sec_lines):
    """remove empty lines at end and at the beginning"""
    result = []
    # empty?
    if len(sec_lines) == 0:
        return result

    # first non-empty
    begin = 0
    for line in sec_lines:
        if len(line) > 0:
            break
        begin += 1

    # last non empty
    last = len(sec_lines) - 1
    for line in reversed(sec_lines):
        if len(line) > 0:
            break
        last -= 1

    return sec_lines[begin : last + 1]


def get_min_indent(lines):
    min_indent = 80
    for line in lines:
        n = len(line)
        if n > 0:
            indent = get_indent(line)
            if indent < n and indent < min_indent:
                min_indent = indent
    return min_indent


def deindent_sec_lines(sec_lines):
    indent = get_min_indent(sec_lines)
    result = []
    for line in sec_lines:
        n = len(line)
        if n > 0:
            line_indent = get_indent(line)
            if line_indent == n:
                # line with only spaces?
                line = ""
            else:
                line = line[indent:]
        result.append(line)
    return result


def add_section(page, sec_name, sec_lines):
    # add current first
    sec_lines = remove_empty_sec_lines(sec_lines)
    if len(sec_lines) > 0:
        sec_lines = deindent_sec_lines(sec_lines)
        page.add_section(sec_name, sec_lines)
        logging.debug("add section '%s' with %d lines", sec_name, len(sec_lines))
    # keep empty names sections
    elif sec_name != "":
        page.add_section(sec_name, [])
        logging.debug("add empty section '%s'", sec_name)


def parse_page(title, lines):
    """parse lines of a page and extract sections"""

    page = AutoDocPage(title)

    # keep raw page
    raw_page = "\n".join(lines)
    page.set_raw_page(raw_page)

    sec_name = ""
    sec_lines = []
    header_indent = 0

    # split into sections
    for line in lines:
        line = cleanup_line(line)
        indent = get_indent(line)
        if indent == 0:
            # empty line
            sec_lines.append(line)
        else:
            # try to get a new section header
            header = get_section_header(line, indent)
            if header:
                do_add_section = True
                if header_indent == 0:
                    # on first section keep header indent
                    header_indent = indent
                    logging.debug("section indent=%s", header_indent)
                else:
                    # otherwise check if indent matches
                    if indent != header_indent:
                        # no seems to be no section header
                        sec_lines.append(line)
                        logging.debug("no section header: '%s'", header)
                        do_add_section = False
                # really add as a section
                if do_add_section:
                    add_section(page, sec_name, sec_lines)
                    # start new section
                    sec_name = header
                    sec_lines = []
            else:
                # append to current section
                sec_lines.append(line)

    # add last section
    add_section(page, sec_name, sec_lines)

    return page


def parse_autodoc(file_name):
    """parse autodoc and split into sections.
    return AutoDoc"""

    # read full file
    with open(file_name, encoding="latin-1") as fh:
        data = fh.read()

    # split into lines
    lines = data.split("\n")
    num = len(lines)
    if num == 0:
        return None

    # read TOC
    toc = []
    if lines[0] != "TABLE OF CONTENTS":
        raise ParseError("No TOC header!")
    pos = 2
    while lines[pos][0] != "\f":
        line = lines[pos]
        toc.append(line)
        pos += 1

    # build autodoc
    doc = AutoDocBook(file_name)

    # store topics, i.e. front part of title "foo/bar" -> topic is "foo"
    topics = set()

    # parse sections
    toc_pos = 0
    while pos < num:
        # section title
        line = lines[pos]

        # assume page title starts with form feed
        if line[0] != "\f":
            raise ParseError("No section form feed!")
        # eof
        if len(line) == 1:
            break
        pos += 1

        # make sure page title matches toc entry
        title = line[1:]
        exp_title = toc[toc_pos]
        if not title.startswith(exp_title):
            raise ParseError(f"Wrong section {title} != {exp_title}")
        toc_pos += 1

        # read in page
        page_lines = []
        while True:
            if pos == num:
                break
            line = lines[pos]
            if len(line) > 0 and line[0] == "\f":
                break
            page_lines.append(line)
            pos += 1

        # parse page
        page = parse_page(exp_title, page_lines)
        page.set_book(doc)

        # add to doc
        doc.add_page(exp_title, page)

        # extract topic
        topic, _ = exp_title.split("/")
        topics.add(topic)

    # add topics to document
    for topic in sorted(topics):
        doc.add_topic(topic)

    return doc
