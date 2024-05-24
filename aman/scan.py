import os
import time
import logging


def scan_autodocs(base_dir, doc_class):
    """scan a directory for *.doc autodoc files and return list of AutoDocs"""
    result = []
    num = 0
    start = time.monotonic()
    for file in os.listdir(base_dir):
        if file.endswith(".doc"):
            path = os.path.join(base_dir, file)
            stat = os.stat(path)
            mtime = stat.st_mtime
            name, _ = os.path.splitext(file)
            result.append(doc_class(name, path, mtime))
            num += 1
    end = time.monotonic()
    logging.info("scanned '%s' (%s files) in %.6f", base_dir, num, end - start)
    return result


def scan_cache(cache_dir, autodocs, zip):
    """scan the cache directory for the autodocs"""
    for adoc in autodocs:
        name = adoc.get_name()
        cache_file = os.path.join(cache_dir, name + ".json")
        if zip:
            cache_file += ".gz"
        if os.path.exists(cache_file):
            mtime = os.stat(cache_file).st_mtime
        else:
            mtime = 0
        adoc.set_cache_file(cache_file, mtime, zip)
        is_valid = adoc.is_cache_valid()
        logging.info("cache '%s' (mtime=%d) valid=%s", cache_file, mtime, is_valid)
