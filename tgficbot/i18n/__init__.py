from . import strings_en
from . import strings_zh_hans
from . import strings_zh_hant

from .. import db

_strings_all = {
    'en': strings_en,
    'zh-hans': strings_zh_hans,
    'zh-hant': strings_zh_hant
}

languages = {'en': 'English', 'zh-hans': '简体中文', 'zh-hant': '繁體中文'}


def I18nHandler(database: db.Database):
    def withi18n(func):
        async def wrapper(event):
            user = await event.get_chat()
            langcode = database.get_user_lang(user.id)
            if langcode in ['follow', None]:
                strings = _strings_all[user.lang_code] \
                    if user.lang_code in _strings_all else strings_en
                return await func(event=event, strings=strings)
            else:
                strings = _strings_all[langcode]
                return await func(event=event, strings=strings)

        return wrapper

    return withi18n


def with_telegram_i18n(func):
    async def wrapper(event):
        user = await event.get_chat()
        strings = _strings_all[user.lang_code] \
            if user.lang_code in _strings_all else strings_en
        return await func(event=event, strings=strings)

    return wrapper
