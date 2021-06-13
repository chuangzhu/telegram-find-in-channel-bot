MessagesEachSearch = 10


class CQ:
    """
    Callback Queries
    """
    FindShowMorePrefix = 'fsm'
    # digest: the md5 digest of the search, start: next start
    FindShowMore = FindShowMorePrefix + ':{digest}:{start}'

    # TODO: also add prefixes for these callback queries
    SelectAChannelToFindPrefix = 'scf'
    SelectAChannelToFind = SelectAChannelToFindPrefix + ':{channel_id}'

    SetLangPrefix = 'sll'
    SetLang = SetLangPrefix + ':{langcode}'
