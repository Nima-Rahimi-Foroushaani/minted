from importlib import import_module
from pygments.util import ClassNotFound

# Map lexer names to corresponding module files and lexer class names
LOCAL_LEXERS = {
    'rust_vf': {'mod': 'lexer_rust_vf', 'cls': 'RustVfLexer'}
}


def find_local_lexer_class_by_name(lexer_name):
    lexer_info = LOCAL_LEXERS.get(lexer_name)
    if not lexer_info:
        raise ClassNotFound(lexer_name)
    try:
        lexer_module = import_module(rf'''.{lexer_info['mod']}''', package=__name__)
        return getattr(lexer_module, lexer_info['cls'])
    except Exception as e:
        raise ImportError(rf'''Failed to load lexer {lexer_name!r}: {e}''')