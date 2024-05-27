# aman - Read Amiga autodocs like man pages

This little tool allows you to read your Amiga NDK's `autodoc` documentation
on your modern system with a Un*x `man page` like interface.

## Quick Start

Just give a function name you need information on and you get the
documentation page instantly:

    ❯ aman GetMsg
    exec.library/GetMsg

    NAME
            GetMsg -- get next message from a message port

    SYNOPSIS
            message = GetMsg(port)
            D0         A0

            struct Message *GetMsg(struct MsgPort *);

    FUNCTION
            This function receives a message from a given message port. It
            provides a fast, non-copying message receiving mechanism. The
            received message is removed from the message port.
    ...
    
It will show documentation for exec's `GetMsg()` call. 

By default your pager (set by `MANPAGER` or `PAGER` env variable) will be used
for browsing the documents. Use `--no-pager` option to write the output to
your console directly.

You could also search for references (aka SEE ALSO) of a function name:

    > aman -s send
    bsdsocket.library/-icmp-
    bsdsocket.library/-ip-
    bsdsocket.library/-udp-
    bsdsocket.library/ObtainSocket
    bsdsocket.library/ReleaseCopyOfSocket
    bsdsocket.library/ReleaseSocket
    bsdsocket.library/SetSocketSignals
    bsdsocket.library/socket
    bsdsocket.library/WaitSelect

## Installation

The `aman` tool can be installed with

    pip install aman

The only step missing is to tell `aman` where the Amiga NDK autodocs are
located:

    export AMANPATH=/my/path/to/NDK/autodocs:/my/path/to/NDK/sana+roadshowtcp-ip/doc

or you create a config file in `$HOME/.aman/config.json`:

    {
            "aman_config": 1,
            "man_paths" : [
                    "/my/path/to/NDK/autodocs",
                    "/my/path/to/NDK/sana+roadshowtcp-ip/doc"
            ]
    }
 
## Reference Manual

### Terms

To better understand the options of `aman` a few terms need to be defined:

  * A single *book* is contained in an *autodoc* file with extension `*.doc`.
    A book starts with a table of contents (TOC) and is followed by *pages*.
  * Each *page* in a *book* contains a description of a function or more
    informational contents. A page contains a heading with a *topic* and a
    *title* separated by a slash.
  * *Topics* in a *book* structure the pages. Typically a *book* contains only
    pages of a single topic. E.g. the `exec` book only contains pages with the
    `exec.library` topic. In some books multiple topics are found.
  * The *title* of a page gives the function name of a page describing a
    function. A more generic title is used for informational content.
  * A *page* is composed of a set of *sections*. The *section* structure on
    each page in a book is typically the same but may differ between books.
    Same named *sections* provide similar content, e.g. a *NAME* section
    always gives the name of a function. Common sections are NAME, SYNOPSIS,
    SEE ALSO.

### Command Line Options

#### Common Options

`aman` offers a large set of options that can adjust the operation of the
tool. Call `aman -h` to see all options.

    options:
      -h, --help            show this help message and exit
      -v, --verbose         be more verbose

Use `-v` to see internal details on the operation of `aman`. Repeat `-v` to
increase the verboseness.

#### Mode Options

    mode options:
      -b, --list-books      show available books and quit
      -p LIST_PAGES, --list-pages LIST_PAGES
                            show available pages of a given book and quit

`aman` can operate in different modes: By default the search mode is active.
In search mode keywords are searched in the autodocs and the resulting pages
are shown.

The `-b` options lists all books found in the `aman_paths` and a list with the
book name and the contained topics is given. If the topic and the book have
the same name then the topic is omitted:

    > aman -b
    8svx_dtc             8svx.datatype
    acbm_dtc             acbm.datatype
    amiga_lib            amiga.lib
    amigaguide           amigaguide.library
    amigaguide_dtc       amigaguide, amigaguide.class
    anim_dtc             anim.datatype
    animation_dtc        anim.datatype, animation.datatype
    arexx_cl
    ...

The `-p` option lists the pages of a book. Just give a name of a book and a
list with the topic/title of each page is given:

    > aman -p cia
    cia.resource/AbleICR
    cia.resource/AddICRVector
    cia.resource/RemICRVector
    cia.resource/SetICR

#### Search Options

    search options:
      keywords              keywords to search for
      -i, --ignore-case     ignore case in keyword match
      -t, --topic           search with 'topic/keyword'
      -s, --see-also        search in SEE ALSO section
      -f FULL_SECTION, --full-section FULL_SECTION
                            full text search in given SECTION of page
      -F, --full-page       full text search in page
      -B LIMIT_BOOKS, --limit-books LIMIT_BOOKS
                            only search in these books (list seperated by colon)

In search mode you need to give one or more `keywords`. Each keyword is
searched and the found pages are shown.

By default the search is case sensitive, i.e. the keyword must match exactly.
If you specify the `-i` option then matches are found ignoring the case.

The following different search modes are available:

  * No option: the keyword has to match the *title* of a page, e.g. `AllocMem`
    will find the AllocMem function.
  * `-t` option: the keyword has to match the *topic/title* of a page, e.g.
    `exec.library/AllocMem` is required to match the AllocMem function.
  * `-s` option: the keyword has to match one entry in the *SEE ALSO* section
    of a page. E.g. `aman -s send` will return all pages that refer to the
    send function.
  * `-f section` option: The keyword is searched in the given *section* on
    each page of all books. This is a full text search and considerably slower
    than the index based searches above.
  * `-F` option: The keyword is searched in all pages of each book. This full
    text search is a slow operation.

The `-B` option allows to limit the search on a set of books only. Just give a
colon-separated list of books. Use the `-b` option to find out the names of
books available.

### Output Options

    output options:
      -N, --no-pager        disable pager
      -P PAGER, --pager PAGER
                            pager command line
      -a, --all-pages       show multiple results as pages and no list
      -r, --raw-page        show raw page of autodoc otherwise reformat and colorize
      --color               use colorful output
      --no-color            disable colorful output
      -j, --json            output in json format

By default the pages are output via a pager program if a tty is detected as
output device. Otherwise the output is written directly to stdout.

If multiple pages are found then a list of the matches is shown by default. If
you want to see the pages instead then use the `-a` option.

A page is rendered from the interal representation in `aman`. If possible on a
terminal then also some color or display attributes are applied. If you give
the `-r` option then the original formatting is preserved. Coloring can be
adjusted with `--color` or `--no-color` if the auto detection does not work.

If a tty is found and the `-N` option is given then the output is also written
directly to stdout. The `-P` option allows you to specify the pager command to
display the pages. The command has to accept the page input via stdin.

The `-j` option allows you to output a page in the internal JSON structure
used to store pages. This output might be useful if you want to post-process
the pages.

### Config Options

    config options:
      -M MAN_PATH, --man-path MAN_PATH
                            Define the paths of the Amiga autodocs
      -C CACHE_DIR, --cache-dir CACHE_DIR
                            directory for cache files
      -c CONFIG_FILE, --config-file CONFIG_FILE
                            config file
      --dump-config         dump current config into file
      -R, --rebuild-cache   force recreation of index cache

These options allow you to configure `aman`. Most of these options don't need
adjustment on the command line (`-M` or `-C`). You better set them via
environment variables or in the config file (see below).

With `-c` you can choose another location for the config file. The default
is `$HOME/.aman/config.json`. The `--dump-config` command will create this
file for you if it does not exist yet. Adapt this template to your needs.

The `-R` option is only needed if the cache files are in an inconsistent state
and need to be rebuild. Note that only the indices in the cache are rebuild
that are needed for the current search. A better way to completely clean the
cache is to wipe the cache directory (default: `$HOME/.aman/cache/`).

### Configuration

`aman` can be configured in three different ways:

  * from a config file (`$HOME/.aman/config.json`)
  * via environment variables
  * with command line options (see above)

An option defined in a later stage overwrites the previous setting.

#### Json Config File

You can write the options into a JSON config file located at
`$HOME/.aman/config.json`:

    {
      "aman_config": 1,
      "man_paths": [ /path/to/autodocs, /more/paths/to/autodocs ],
      "cache_dir": "/path/to/cache",
      "pager": "/usr/bin/less -R --use-color -Ddg -Du+y"
    }

The version tag `aman_config` is required otherwise the config file is not
accepted. The other options are similar to the command line options.

#### Environment Variables

The following variables in the environment are used to configure `aman`:

| Variable    | Description     |
| --------    | --------------- |
| `AMANPATH`  | list of autodoc directories, separated by '`:`' | 
| `AMANCACHE` | directory of cache files (default `~/.aman/cache`) |
| `MANPAGER`  | set the default display program |
| `PAGER`     | set the default display program (if no `MANPAGER`) is given |
