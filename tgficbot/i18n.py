import os
import gettext
from . import db

LOCALEDIR = os.path.join(os.path.dirname(__file__), 'locales')
langcodes = [
    f for f in os.listdir(LOCALEDIR)
    if os.path.isdir(os.path.join(LOCALEDIR, f))
]
translates = {
    lang: gettext.translation('main', LOCALEDIR, [lang])
    for lang in langcodes
}
languages = {lang: translates[lang].info()['language'] for lang in langcodes}


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
                return await func(event=event, _=translate_telegram.gettext)

            db_lang = database.get_user_lang(user.id)
            if db_lang in ['follow', None]:
                return await func(event=event, _=translate_telegram.gettext)
            return await func(event=event, _=translates[db_lang].gettext)

        return wrapper

    return withi18n
