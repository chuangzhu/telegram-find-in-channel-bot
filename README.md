# [@FindInChannelBot](https://telegram.me/FindInChannelBot)

Telegram 的消息搜索功能不支持中日韩等语言，因为这类语言字词间不加空格。而我习惯于使用 Telegram 的频道做笔记，因此一个好用的搜索功能对我来说很重要。为了能方便地在频道内搜索，这个机器人诞生了。

The ‘Find in Conversations’ feature in Telegram does not support searching in languages like Chinese/Japanese/Korean etc., since these languages do not have spaces between words. I'm used to take notes in Telegram channels, so it's important for me to have a better search tool. I made this bot so I can find in channels easily.

## Usage

`/start` the bot  
`/add` a channel to the bot  
`/find` in the channel  
`/lang` setting UI language  
`/cancel` the current action  
`/help` show help

The user interface language of this bot follows your Telegram settings by default (language packs on Telegram desktop, and system language settings on mobiles). [Please help with translating](./tgficbot/locales/)!

## Deploy

Instead of HTTP bot API, this bot uses MTProto client API. Please obtain these tokens:

* App `api_id` and `api_hash`, please obtain it at https://my.telegram.org/apps;
* Bot token, please obtain it by talking to [@BotFather](https://t.me/BotFather).

You can install it via PyPI:

```sh
pip3 install -U telegram-find-in-channel-bot
```

<details><summary>Or clone this repo and install from source:</summary>

```sh
cd telegram-find-in-channel-bot
for f in tgficbot/locales/*.po; do
    mkdir -p ${f%.po}/LC_MESSAGES
    msgfmt $f -o ${f%.po}/LC_MESSAGES/main.mo
done
python3 setup.py install
```

Run `apt install gettext` if command `msgfmt` not found.

</details>

(Optional) If `cryptg` is installed, the bot will work faster:

```sh
apt update
apt install clang python3-dev
pip3 install -U cryptg
```

Configuration file is by default `~/.config/tgficbot.cfg`, but you can specify a different location. Here's the format:

```ini
[api]
id = 123456
hash = xxxxxxxxxxxxxxxxx

[bot]
token = 123456789:xxxxxxxxxxxxxxxxxxxx
```

To run:

```sh
python3 -m tgficbot.main --config <config_file> --dbpath <directory_to_store_database>
```

The parameter following `--dbpath` indicates where the databases are stored. They are in `~/.cache/` if you don't specify `--dbpath`.
