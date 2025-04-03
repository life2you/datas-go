#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
启动脚本
"""

import sys
from src.main import main

if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main())) 