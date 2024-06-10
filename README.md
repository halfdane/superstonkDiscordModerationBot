# Superstonk moderation bot for discord

# Preconditions
- The bot is written in `python3`
- The user service config (used for automatic restarts and automated deployment) is only tested on `Ubuntu`
- Automated deployment uses `git` and `ssh`

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

# Automated deployment
The bot is deployed using github actions. The workflow is triggered on every push to the main branch.
To deploy to a new server, the following steps are necessary:
- Prepare passwordless login to the server using ssh_keys
- Create a new environment in the github settings of the repository
- Create `HOST`, `USERNAME` and `SSH_KEY` environment secrets
- Adjust the `.github/workflows/ssh_deploy.yml` file to use the new environment
  Either by adding a new deployment step or by changing the existing one

