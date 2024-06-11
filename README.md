# Superstonk moderation bot for discord

Contains the flairy, the qvBot and several other moderation tools for the Superstonk discord server.

# Preconditions
- Ubuntu for the user service (used for automatic restarts and automated deployment)
- `git` for initial checkout and automated deployment
- `ssh` server for automated deployment and remote administration
- `python3` for the bot itself
- `build-essential` to get the `make` command
- `nano` or another text editor to adjust the configuration

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
- If everything works, you can now install and start the bot as a user service (tested only on Ubuntu)
    `make install`
    (Needs sudo rights to allow the bot to keep running after you log out)
- Watch the logs
    `journalctl --user-unit superstonkModerationBot.service -f`
- 

# Automated deployment
The bot is deployed using github actions. The workflow is triggered on every push to the main branch.
To deploy to a new server, the following steps are necessary:
- Prepare passwordless login to the server using ssh_keys
- Create a new environment in the github settings of the repository
- Create `HOST`, `USERNAME` and `SSH_KEY` environment secrets
- Adjust the `.github/workflows/ssh_deploy.yml` file to use the new environment
  Either by adding a new deployment step or by changing the existing one

