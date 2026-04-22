# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：main.py
# @Date   ：2026/1/10 00:00
# @Author ：leemysw
#
# 2026/1/10 00:00   Create
# =====================================================

import warnings

warnings.filterwarnings("ignore", category=UserWarning)

from feishu_docx.cli.main import app

if __name__ == '__main__':
    app()
