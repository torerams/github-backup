# GitHub and Bitbucket backup script

This directory contains a script, `backup.py`, for backing up GitHub and Bitbucket repositories.

The script requires a GitHub and Bitbucket token and a destination directory. It then uses the token to populate the destination directory with clones of all the repositories the token can access.

Repeated runs only update the already existing backups and add new repositories, if any.

## Installation

Install the required Python dependencies using `pip3`:

```
$ pip3 install -r requirements.txt
```

## Configuring

### Create a token

For authorization you need to create a new personal GitHub token. You can do this from the GitHub settings, under the **Personal Access Tokens** tab.

![Step 1](images/new-token-1.png)

When you click the **Generate new token** button you enter the token creation screen. Here you should give the token a descriptive name and choose its *scopes*, which basically determine what the token is allowed to do.

![Step 2](images/new-token-2.png)

To backup public and private repositories you need to select only the **repo** scope. If you have no need for private repositories just choose the **public_repo** scope.

![Step 3](images/new-token-3.png)

After clicking the **Generate token** button you're presented with the generated token. Remember to store it now, as GitHub won't show it to you anymore!

In the next example let's assume your token is `6b86190dd45c57c1a1b039a5a54d892e019102f7` as in the above image.

### Create a configuration file

To run the script you need a JSON configuration file. For an example see the included file `config.json.example`.

As an example let's create a file, `config.json`. This file should contain the token we just created and the destination directory where we want to back up the repositories:

```
{ "repositories" : [
    { "type": "github",
      "token": "<github token>",
      "directory": "<github>",
      "owners": ["<owner1>", "<owner2>"]},
    { "type": "bitbucket",
      "token": "<bitbucket app password>",
      "directory": "<bitbucket>",
      "user": "<bitbucket username>",
      "workspace": "<bitbucket workspace>"}
],
 "repeat": "1440"
}
```

Repeat can be added to make the script run forever at repeat minutes interval.
Remove the repeat or set to 0 to run the script only once.

## Running

Two environment variables should be set before running the script

```
export CONFIG_FILE="<my config.json file>"
export BACKUP_DIR="<backup dir>"
```

If these environment variables are not set, then they will be set to Docker friendly
values CONFIG_FILE=/config, and BACKUP_DIR=/backup.

After preparing the token and the configuration file you now can run the script:

```
$ python3 backup.py
```

## Docker

You can use a docker image to run the backup script inside a Docker container.
Map volume to /backup and /config.

Example of command line:

```
docker run --rm -it -v ${PWD}/../backups:/backup -v ${PWD}/../config:/config torerams/git-backup:1.0
```

## Synology NAS

The Docker container can be run on a Synology NAS using the Container Manager.

Example of YAML configuration:

```
version: '1.0'
services:
  backup-service:
    image: torerams/git-backup:1.0
    restart: always
    container_name: git-backup
    volumes:
      - /volume1/backups/git-backup:/backup
      - /volume1/docker/git-backup/config:/config
    environment:
      - TZ=Europe/Oslo
```
