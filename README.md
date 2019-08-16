# [@FindInChannelBot](https://telegram.me/FindInChannelBot)

Telegram 的消息搜索功能不支持中日韩等语言，因为这类语言字词间不加空格。而我习惯于使用 Telegram 的频道做笔记，因此一个好用的搜索功能对我来说很重要。为了能方便地在频道内搜索，这个机器人诞生了。

The ‘Find in Conversations’ feature in Telegram does not support searching in Chinese/Japanese/Korean etc., since these languages do not have spaces between words. I'm used to take note in Telegram channels, so it's important for me to have a better search tool. So I made this bot so I can find in channels easily.

## Usage

`/start` `/add` `/find`

## 部署

这个机器人使用的并不是 HTTP bot API，而是 MTProto 客户端 API。请先获取这两样东西：

* App `api_id` 和 `api_hash`，请在 https://my.telegram.org/apps 获取；
* Bot token，请与 [@BotFather](https://t.me/BotFather) 聊天获取。

克隆这个仓库，然后安装：  

```sh
cd telegram-find-in-channel-bot
python3 setup.py install
```

（可选）安装 `cryptg` 可提速：

```sh
apt update
apt install clang python3-dev
pip3 install -U --user cryptg
```

配置文件位置在 `~/.config/tgficbot.cfg`，格式如下：

```ini
[api]
id = 123456
hash = xxxxxxxxxxxxxxxxx

[bot]
token = 123456789:xxxxxxxxxxxxxxxxxxxx
```

准备好配置文件后，就可以启动了：

```sh
python3 -m tgficbot.main
```

运行时的数据库将被放在 `~/.cache/tgficbot.db`。

## Deploy

Instead of HTTP bot API, this bot uses MTProto client API. Please obtain these tokens:

* App `api_id` and `api_hash`, please obtain it at https://my.telegram.org/apps;
* Bot token, please obtain it by talking to [@BotFather](https://t.me/BotFather).

Clone this repo and install:

```sh
cd telegram-find-in-channel-bot
python3 setup.py install
```

(Optional) If `cryptg` is installed, the bot will work faster:

```sh
apt update
apt install clang python3-dev
pip3 install -U --user cryptg
```

Configuration file is `~/.config/tgficbot.cfg`, here's the format:

```ini
[api]
id = 123456
hash = xxxxxxxxxxxxxxxxx

[bot]
token = 123456789:xxxxxxxxxxxxxxxxxxxx
```

To run:

```sh
python3 -m tgficbot.main
```

The database will be placed at `~/.cahce/tgficbot`.
