from typing import Final
import importlib.util
from importlib.metadata import version


def is_editable_install():
    try:
        spec = importlib.util.find_spec('xivapy')
        if spec and spec.origin:
            return 'site-packages' not in spec.origin
    except Exception:
        # Assume dev?
        return True
    # Assume dev
    return True


VERSION: Final[str] = 'dev' if is_editable_install() else version('xivapy')
