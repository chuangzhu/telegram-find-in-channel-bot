import os
import gettext
from .. import db

LOCALEDIR = os.path.join(os.path.dirname(__file__), '..', 'locales')
languages = ['en', 'zh-hans', 'zh-hant']
translates = {
    'en': gettext.translation('tgficbot', LOCALEDIR, languages=['en']),
    'zh-hans': gettext.translation('tgficbot', LOCALEDIR, languages=['zh-hans']),
    'zh-hant': gettext.translation('tgficbot', LOCALEDIR, languages=['zh-hant']),
}


def I18nHandler(database: db.Database):
    def withi18n(func):
        async def wrapper(event):
            if not event.is_private:
                return await func(event=event, _=translates['en'].gettext)

            user = await event.get_chat()
            translate_telegram = translates[user.lang_code] \
                if user.lang_code in translates else translates['en']

            # When a user /start the bot for the 1st time
            if database.get_user_state(user) is None:
                return await func(event=event, strings=translate_telegram)

            db_lang = database.get_user_lang(user.id)
            if db_lang in ['follow', None]:
                return await func(event=event, _=translate_telegram)
            return await func(event=event, _=translates[db_lang])

        return wrapper

    return withi18n
