from davos.core.core import smuggle, smuggle_parser

# TODO: add __all__

def _activate_helper(smuggle_func: smuggle, parser_func: smuggle_parser) -> None: ...
def _deactivate_helper(smuggle_func: smuggle, parser_func: smuggle_parser) -> None: ...
