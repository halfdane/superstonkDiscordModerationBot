# Superstonk moderation bot for discord

# Installation
- Check out the repository
    `git clone https://github.com/halfdane/superstonkDiscordModerationBot.git`
- Change into the directory
    `cd superstonkDiscordModerationBot`
- Install the dependencies and start the bot  
    `make`
- the first run will fail, so you have to adjust the newly created `config.json` file
    `nano config.json`
- Run the bot once more and check if it works
    `make`
- If everything works, you can now install and start the bot as a user service
    `make install`
- Watch the logs
    `journalctl -u superstonkDiscordModerationBot -f`


