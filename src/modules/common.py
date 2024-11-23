"""common.py"""
from prompt_toolkit.completion import WordCompleter

SYSTEM_STRINGS: list[str] = ['back','clear','cls','help','exit']

def fix_selection(function_name) -> str:
    """Fix the selection if it is a system command.
    
    Args:
        function_name: The string to check.

    Returns:
        The fixed string.
    """
    for string in SYSTEM_STRINGS:
        if string in function_name:
            return f"_{function_name}"
    return function_name

def word_completer(obj) -> WordCompleter:
    """Automatically generate words to use as commands.
    
    Args:
        obj: The object to generate words from.
    
    Returns:
        The list of available words that can be used.
    """
    words: list[str] = sorted([func for func in dir(obj) if callable(getattr(obj, func)) and not func.startswith('_')])
    words.append('back')
    words.append('help')
    words.append('exit')
    return WordCompleter(words)
