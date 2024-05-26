import os
import json
import logging

JSON_VERSION = 1
VERSION_TAG = "aman_config"
MAN_PATHS_TAG = "man_paths"
CACHE_DIR_TAG = "cache_dir"
PAGER_TAG = "pager"

AMAN_DEFAULT_CACHE_DIR = "~/.aman/cache"
AMAN_ENV_PATH_VAR = "AMANPATH"
AMAN_ENV_CACHE_VAR = "AMANCACHE"
AMAN_ENV_MANPAGER_VAR = "MANPAGER"
AMAN_ENV_PAGER_VAR = "PAGER"

ENV_DESC = f"""
environment variables:

AMANPATH   list of autodoc directories, separated by '{os.pathsep}'
AMANCACHE  directory of cache files ({AMAN_DEFAULT_CACHE_DIR})
MANPAGER   or
PAGER      set the default display program
"""


class Config:
    def __init__(self, config_file=None, use_env=True):
        self.man_paths = []
        self.cache_dir = None
        self.pager = None
        self._set_default()
        if use_env:
            self._set_env()
        if config_file and os.path.exists(config_file):
            self._load_config(config_file)
        else:
            logging.debug("config: no file at '%s'", config_file)

    def _set_default(self):
        self.cache_dir = os.path.expanduser(AMAN_DEFAULT_CACHE_DIR)

    def _set_env(self):
        logging.debug("config: from env")
        # man path
        if AMAN_ENV_PATH_VAR in os.environ:
            self.man_paths = os.environ[AMAN_ENV_PATH_VAR].split(os.pathsep)
        # cache dir
        if AMAN_ENV_CACHE_VAR in os.environ:
            self.cache_dir = os.environ[AMAN_ENV_CACHE_VAR]
        # pager
        if AMAN_ENV_PAGER_VAR in os.environ:
            self.pager = os.environ[AMAN_ENV_PAGER_VAR]
        if AMAN_ENV_MANPAGER_VAR in os.environ:
            self.pager = os.environ[AMAN_ENV_MANPAGER_VAR]

    def _load_config(self, config_file):
        logging.debug("config: loading '%s'", config_file)
        with open(config_file) as fh:
            data = json.load(fh)
        # check version
        if VERSION_TAG not in data:
            logging.error("Config file '%s' has no '%s'!", config_file, VERSION_TAG)
            return False
        if data[VERSION_TAG] != JSON_VERSION:
            logging.error(
                "Config fila has wrong version: %s ! = %s",
                data[VERSION_TAG],
                JSON_VERSION,
            )
            return False
        # retrieve values
        if MAN_PATHS_TAG in data:
            self.man_paths = data[MAN_PATHS_TAG]
        if CACHE_DIR_TAG in data:
            self.cache_dir = data[CACHE_DIR_TAG]
        if PAGER_TAG in data:
            self.pager = data[PAGER_TAG]
        return True

    def dump(self, config_file):
        data = {
            VERSION_TAG: JSON_VERSION,
            MAN_PATHS_TAG: self.man_paths,
            CACHE_DIR_TAG: self.cache_dir,
            PAGER_TAG: self.pager,
        }
        logging.info("config is: %s", data)
        with open(config_file, "w") as fh:
            json.dump(data, fh, indent=2)

    def add_man_path(self, man_path):
        self.man_paths.append(man_path)

    def set_man_path(self, man_paths):
        self.man_paths = man_paths

    def set_cache_dir(self, cache_dir):
        self.cache_dir = cache_dir

    def set_pager(self, pager):
        self.pager = pager

    def get_cache_dir(self):
        return self.cache_dir

    def get_man_paths(self):
        return self.man_paths

    def get_pager(self):
        return self.pager

    def finalize(self):
        # ensure a man path
        if len(self.man_paths) == 0:
            logging.fatal("No path for autodocs given!")
            return False
        # ensure cache dir
        if not os.path.isdir(self.cache_dir):
            logging.debug("config: creating cache dir '%s'", self.cache_dir)
            os.makedirs(self.cache_dir)
        # all fine
        logging.debug("config: finalized")
        return True
