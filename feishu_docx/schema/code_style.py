# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：code_style.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: None
[OUTPUT]: 对外提供 CODE_STYLE_MAP 代码语言映射表
[POS]: schema 模块的静态配置，被 parsers.document 使用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

# 飞书代码块语言类型 -> Markdown 语言标识符
CODE_STYLE_MAP = {
    1: "plaintext",
    2: "abap",
    3: "ada",
    4: "apache",
    5: "apex",
    6: "asm",
    7: "bash",
    8: "csharp",
    9: "cpp",
    10: "c",
    11: "cobol",
    12: "css",
    13: "coffeescript",
    14: "d",
    15: "dart",
    16: "delphi",
    17: "django",
    18: "dockerfile",
    19: "erlang",
    20: "fortran",
    21: "foxpro",
    22: "go",
    23: "groovy",
    24: "html",
    25: "htmlbars",
    26: "http",
    27: "haskell",
    28: "json",
    29: "java",
    30: "javascript",
    31: "julia",
    32: "kotlin",
    33: "latex",
    34: "lisp",
    35: "logo",
    36: "lua",
    37: "matlab",
    38: "makefile",
    39: "markdown",
    40: "nginx",
    41: "objectivec",
    42: "openedge",
    43: "php",
    44: "perl",
    45: "postscript",
    46: "powershell",
    47: "prolog",
    48: "protobuf",
    49: "python",
    50: "r",
    51: "rpg",
    52: "ruby",
    53: "rust",
    54: "sas",
    55: "scss",
    56: "sql",
    57: "scala",
    58: "scheme",
    59: "scratch",
    60: "shell",
    61: "swift",
    62: "thrift",
    63: "typescript",
    64: "vbscript",
    65: "vb",
    66: "xml",
    67: "yaml",
    68: "cmake",
    69: "diff",
    70: "gherkin",
    71: "graphql",
    72: "glsl",
    73: "properties",
    74: "solidity",
    75: "toml",
}

CODE_STYLE_MAP_REVERSE = {v: k for k, v in CODE_STYLE_MAP.items()}