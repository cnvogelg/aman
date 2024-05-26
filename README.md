# aman - Read Amiga autodocs like man pages

This little tool allows you to read your Amiga NDK's `autodoc` documentation
on your modern system with a Un*x `man page` like interface:

Just give a function name you need information on and you get the documentation
page:

    aman GetMsg
    
It will show documentation for exec's `GetMsg()` call.

## Installation

The `aman` tool can be installed with

    pip install aman

The only step missing is to tell `aman` where the NDK autodocs are located:

    export AMANPATH=/my/path/to/NDK/autodocs
    
