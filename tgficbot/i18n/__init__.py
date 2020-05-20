from . import strings_en
from . import strings_zh_hans

strings_all = {'en': strings_en, 'zh-hans': strings_zh_hans}


def withi18n(func):
    async def wrapper(event):
        user = await event.get_chat()
        strings = strings_all[user.lang_code]
        return await func(event=event, strings=strings)

    return wrapper