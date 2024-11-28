from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from pygments.lexers.sql import SqlLexer

sql_completer = WordCompleter([
    'abort', 'action', 'add', 'after', 'all', 'alter', 'analyze', 'and',
    'as', 'asc', 'attach', 'autoincrement', 'before', 'begin', 'between',
    'by', 'cascade', 'case', 'cast', 'check', 'collate', 'column',
    'commit', 'conflict', 'constraint', 'create', 'cross', 'current_date',
    'current_time', 'current_timestamp', 'database', 'default',
    'deferrable', 'deferred', 'delete', 'desc', 'detach', 'distinct',
    'drop', 'each', 'else', 'end', 'escape', 'except', 'exclusive',
    'exists', 'explain', 'fail', 'for', 'foreign', 'from', 'full', 'glob',
    'group', 'having', 'if', 'ignore', 'immediate', 'in', 'index',
    'indexed', 'initially', 'inner', 'insert', 'instead', 'intersect',
    'into', 'is', 'isnull', 'join', 'key', 'left', 'like', 'limit',
    'match', 'natural', 'no', 'not', 'notnull', 'null', 'of', 'offset',
    'on', 'or', 'order', 'outer', 'plan', 'pragma', 'primary', 'query',
    'raise', 'recursive', 'references', 'regexp', 'reindex', 'release',
    'rename', 'replace', 'restrict', 'right', 'rollback', 'row',
    'savepoint', 'select', 'set', 'table', 'temp', 'temporary', 'then',
    'to', 'transaction', 'trigger', 'union', 'unique', 'update', 'using',
    'vacuum', 'values', 'view', 'virtual', 'when', 'where', 'with',
    'without'], ignore_case=True)

main_list = ['add','select','show','start','stop']
add_list = ['note','target']
target_list = ['add']
all_list = set(main_list + add_list)
all_list = sorted(list(all_list))

main_completer = WordCompleter(main_list)
add_completer = WordCompleter(add_list)
all_completer = WordCompleter(all_list)

main_style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})

def main():
   session = PromptSession(completer=all_completer, style=main_style)
   session_main = PromptSession(completer=main_completer)
   session_add = PromptSession(completer=add_completer)

   while True:
       try:
           text = session.prompt('> ')
       except KeyboardInterrupt:
           continue
       except EOFError:
           break
       else:
           if 'add' == text:
               text = session_add.prompt(f'{text} > ')

   print('Exiting.')

if __name__ == '__main__':
    main()