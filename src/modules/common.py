"""common.py"""
import random
from prompt_toolkit.completion import WordCompleter
from modules.quotes import QUOTES

SYSTEM_STRINGS: list[str] = ['back','clear','cls','help','exit']

def get_quote(category=None) -> str:
    """Get a random quote."""
    quotes = []
    quote = ''
    if category is not None:
        for quote in QUOTES:
            if quote['category'] == category:
                quotes.append(quote)
    else:
        quotes = QUOTES

    if len(quotes) > 0:
        random_index = random.randint(0, len(quotes) - 1)
        random_quote = quotes[random_index]
        quote = f'"{random_quote['quote']}" - {random_quote['author']}\n'

    return quote

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
    words.append('add note')
    words.append('add target')

    words.append('clear')
    words.append('cls')

    words.append('select target')

    words.append('setup database')

    words.append('show tables')
    words.append('show targets')

    words.append('start proxy')
    words.append('stop proxy')

    words.append('help')
    words.append('exit')
    return WordCompleter(words)
