from tgficbot.i18n import strings_en
from tgficbot.i18n import strings_zh_hans
from tgficbot.i18n import strings_zh_hant

def get_multiline(string):
    splitted = string.split('\n')
    lines = [f'"{line}\\n"\n' for line in splitted[:-1]]
    lines.append(f'"{splitted[-1]}"\n')
    lines.insert(0, '""\n')
    return ''.join(lines)


def get_translate(fn, module):
    with open(fn, 'w') as f:
        for msgid in dir(module):
            msgstr = getattr(module, msgid)
            if msgid.startswith('_'):
                continue
            if not isinstance(msgstr, str):
                continue

            linecount = len(msgstr.split('\n'))
            f.write(f'msgid "{msgid}"\n')
            if linecount == 1:
                f.write(f'msgstr "{msgstr}"\n\n')
            else:
                f.write(f'msgstr {get_multiline(msgstr)}\n')

        for k, v in module.help_commands.items():
            f.write(f'''\
msgid "help_command_{k}"
msgstr {get_multiline(v)}
''')

get_translate('tgficbot/locales/en/LC_MESSAGES/tgficbot.po', strings_en)
get_translate('tgficbot/locales/zh-hans/LC_MESSAGES/tgficbot.po', strings_zh_hans)
get_translate('tgficbot/locales/zh-hant/LC_MESSAGES/tgficbot.po', strings_zh_hant)
