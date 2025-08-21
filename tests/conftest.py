import os
import sys


def _add_src_to_path():
    root = os.path.dirname(os.path.dirname(__file__))
    src = os.path.join(root, "src")
    if src not in sys.path:
        sys.path.insert(0, src)


_add_src_to_path()

