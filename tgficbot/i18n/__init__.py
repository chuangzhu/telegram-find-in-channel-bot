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
            if not event.is_private:
                return await func(event=event, strings=strings_en)

            user = await event.get_chat()
            strings_telegram = _strings_all[user.lang_code] \
                if user.lang_code in _strings_all else strings_en

            # When a user /start the bot for the 1st time
            if database.get_user_state(user) is None:
                return await func(event=event, strings=strings_telegram)

            db_lang = database.get_user_lang(user.id)
            if db_lang in ['follow', None]:
                return await func(event=event, strings=strings_telegram)
            return await func(event=event, strings=_strings_all[db_lang])

        return wrapper

    return withi18n
