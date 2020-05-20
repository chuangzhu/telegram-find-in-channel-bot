from . import strings_en
from . import strings_zh_hans
from . import strings_zh_hant

strings_all = {
    'en': strings_en,
    'zh-hans': strings_zh_hans,
    'zh-hant': strings_zh_hant
}


def withi18n(func):
    async def wrapper(event):
        user = await event.get_chat()
        strings = strings_all[user.lang_code] \
            if user.lang_code in strings_all else strings_en
        return await func(event=event, strings=strings)

    return wrapper