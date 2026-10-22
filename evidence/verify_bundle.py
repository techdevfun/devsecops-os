#!/usr/bin/env python3
"""Lệnh kiểm chứng bundle MỘT LỆNH của devsecops-os (tiêu chí nghiệm
thu số 4 của blueprint): kiểm hash toàn bundle theo manifest +
bundle.sha256 và kiểm lại schema M2 của mọi record.

    python3 evidence/verify_bundle.py <thư-mục-bundle>

Mã thật nằm ở bundle_tool.py (cùng thư mục) — file này chỉ là lối
vào ngắn cho đúng hợp đồng "một lệnh duy nhất".
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bundle_tool import main  # noqa: E402

if __name__ == "__main__":
    sys.argv = [sys.argv[0], "verify", *sys.argv[1:]]
    raise SystemExit(main())
