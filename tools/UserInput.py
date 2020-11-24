from typing import Dict
from tools import ColorPrint
from textwrap import wrap


def ask(prompt: str, suggestion: str, type_spec: type, none_allowed: bool):
    """
    Helper function to ask input of specific type from user.
    Suggestion can be given. 'None' can be allowed as a valid input value.
    """
    p = ColorPrint()
    while True:
        if suggestion!='':
            p.print('{prompt} [{!y}{suggestion}{!}]: ', prompt=prompt, suggestion=str(suggestion), end='')
            val = input()
        else:
            p.print('{prompt}: ', prompt=prompt, end='')
            val = input()
        if not val and suggestion!='':
            return suggestion
        if str(val).lower() == 'none' and none_allowed:
            return None
        try:
            return type_spec(val)
        except:
            p.error('{!r}Invalid.')


def choose(text: str, prompt: str, options: Dict[str, str], suggestion: str, none_allowed: bool):
    """
    Helper function to ask user to select from a list of options (with optional description).
    Suggestion can be given. 'None' can be allowed as a valid input value.
    """
    p = ColorPrint()
    key_list = list(options.keys())
    p.print('\n'.join(wrap(text + ':',80)))
    p.print('{!y}[')
    for k in range(len(key_list)):
        elem = key_list[k]
        descr = options[elem]
        if descr:
            p.print('  {!m}#{k}{!} {!y}{elem}{!}:', k=k, elem=elem)
            for line in descr.split('\n'):
                p.print('    {line}', line=line)
        else:
            p.print('  {!m}#{k}{!} {!y}{elem}{!}', k=k, elem=elem)

    p.print('{!y}]')
    p.print('Selection can be made by unique prefix or index.')
    while True:
        val = ask(prompt, suggestion, str, none_allowed)
        if val is None:
            return val
        try:
            index = int(val)
            if index in range(len(key_list)):
                return key_list[index]
            else:
                p.error('{!r}No match for given index.')
        except:
            matches = [key for key in options.keys() if key[:len(val)] == val]
            if len(matches) == 0:
                p.error('{!r}No match for given substring.')
            elif len(matches) > 1:
                p.error('{!r}Selection not unique for given substring.')
            else:
                return matches[0]


