import json
import os
import subprocess
import logging
import sys
import shlex
from termcolor import colored


class PrinterStdout:
    def write(self, data):
        sys.stdout.write(data)

    def close(self):
        pass


class PrinterFile:
    def __init__(self, output):
        self.fobj = open(output, "w")

    def write(self, data):
        self.fobj.write(write)

    def close(self):
        self.fobj.close()


class PrinterPager:
    def __init__(self, pager):
        cmd_line = shlex.split(pager)
        logging.info("launching pager: %s", cmd_line)
        self.proc = subprocess.Popen(cmd_line, stdin=subprocess.PIPE, text=True)

    def write(self, data):
        self.proc.communicate(input=data)

    def close(self):
        self.proc.wait()


class FormatterMono:
    def format_page(self, page):
        lines = page.format_txt_lines()
        data = os.linesep.join(lines)
        return data


class FormatterColor:
    def format_page(self, page):
        lines = []
        title = colored(page.get_title(), attrs=["bold"])
        lines.append(title)
        lines.append("")
        for section in page.get_toc():
            sec_name = colored(section, attrs=["bold"])
            lines.append(sec_name)
            for line in page.get_section(section):
                lines.append("\t" + line)
            lines.append("")
        data = os.linesep.join(lines)
        return data


class Format:
    OUTPUT_FORMAT_TEXT = 0
    OUTPUT_FORMAT_RAW = 1
    OUTPUT_FORMAT_JSON = 2

    def __init__(self):
        self.output_file = None
        self.output_format = self.OUTPUT_FORMAT_TEXT
        self.pager = None
        self.color = False

    def set_output_format(self, output_format):
        self.output_format = output_format

    def set_output_file(self, output_file):
        self.output_file = output_file

    def set_pager(self, pager):
        self.pager = pager

    def set_color(self, color):
        self.color = color

    def _create_printer(self):
        if self.output_file:
            return PrinterFile(self.output_file)
        elif self.pager:
            return PrinterPager(self.pager)
        else:
            return PrinterStdout()

    def format_page_list(self, pages):
        lines = []
        for page in pages:
            lines.append(page.get_title())
        self.format_lines(lines)

    def format_lines(self, lines):
        data = os.linesep.join(lines) + os.linesep
        self.format_data(data)

    def format_page(self, page):
        logging.info("formatting page %s", page)
        if self.output_format == self.OUTPUT_FORMAT_TEXT:
            fmt = self._create_formatter()
            data = fmt.format_page(page)
        elif self.output_format == self.OUTPUT_FORMAT_RAW:
            data = page.get_title() + os.linesep
            data += page.get_raw_page()
        elif self.output_format == self.OUTPUT_FORMAT_JSON:
            data = page.to_json()
            data["title"] = page.get_title()
            data = json.dumps(data, indent=4)

        self.format_data(data)

    def format_data(self, data):
        printer = self._create_printer()
        printer.write(data)
        printer.close()

    def _create_formatter(self):
        if self.color:
            return FormatterColor()
        else:
            return FormatterMono()
