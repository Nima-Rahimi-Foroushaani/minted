from importlib import import_module
from pygments.util import ClassNotFound

# Map style names to corresponding module files and style class names
LOCAL_STYLES = {
    'rust_vf_default': {'mod': 'rust_vf_default', 'cls': 'RustVfDefaultStyle'}
}

def get_local_style_by_name(name):
    style_info = LOCAL_STYLES.get(name)
    if not style_info:
        raise ClassNotFound(name)
    try:
        mod = import_module(rf'''.{style_info['mod']}''', package=__name__)
        return getattr(mod, style_info['cls'])
    except Exception as e:
        raise ImportError(rf'''Failed to load style {name!r}: {e}''')