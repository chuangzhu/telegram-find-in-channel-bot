from typing import NewType

State = NewType('State', int)

Empty = State(0)
AddingAChannel = State(0xa31b2f1f)
SelectingAChannelToFind = State(0x72db58bd)
FindingInAChannel = State(0xfc757945)
SettingLang = State(0xae60c307)


def StateHandler(database):
    def onstate(state: State):
        def decorate(func):
            async def wrapper(event):
                user = await event.get_chat()
                if database.get_user_state(user) == state:
                    return await func(event)
                return

            return wrapper

        return decorate

    return onstate
