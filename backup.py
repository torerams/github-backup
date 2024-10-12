import os
import re
import sys
import json
import errno
import argparse
import subprocess
import urllib.parse
import time

import requests


def get_json(url, token):
    while True:
        response = requests.get(
            url, headers={"Authorization": "token {0}".format(token)}
        )
        response.raise_for_status()
        yield response.json()

        if "next" not in response.links:
            break
        url = response.links["next"]["url"]


def check_name(name):
    if not re.match(r"^\w[-\.\w]*$", name):
        raise RuntimeError("invalid name '{0}'".format(name))
    return name


def mkdir(path):
    try:
        os.makedirs(path, 0o770)
    except OSError as ose:
        if ose.errno != errno.EEXIST:
            raise
        return False
    return True


def mirror(repo_name, repo_url, to_path, username, token):
    parsed = urllib.parse.urlparse(repo_url)
    modified = list(parsed)
    modified[1] = "{username}:{token}@{netloc}".format(
        username=username, token=token, netloc=parsed.netloc
    )
    repo_url = urllib.parse.urlunparse(modified)

    repo_path = os.path.join(to_path, repo_name)
    mkdir(repo_path)

    # git-init manual:
    # "Running git init in an existing repository is safe."
    subprocess.call(["git", "init", "--bare", "--quiet"], cwd=repo_path)

    # https://github.com/blog/1270-easier-builds-and-deployments-using-git-over-https-and-oauth:
    # "To avoid writing tokens to disk, don't clone."
    subprocess.call(
        [
            "git",
            "fetch",
            "--force",
            "--prune",
            "--tags",
            repo_url,
            "refs/heads/*:refs/heads/*",
        ],
        cwd=repo_path,
    )

def backupGitHub(repo, backupDir):
    owners = repo.get("owners")
    token = repo["token"]
    path = os.path.expanduser(repo["directory"])
    path = os.path.join(backupDir, path)
    print("Backing up from GitHub:")
    if mkdir(path):
        print("Created directory {0}".format(path), file=sys.stderr)

    user = next(get_json("https://api.github.com/user", token))
    print("Logged in as user: " + user["login"])
    for page in get_json("https://api.github.com/user/repos", token):
        for repo in page:
            name = check_name(repo["name"])
            owner = check_name(repo["owner"]["login"])
            clone_url = repo["clone_url"]

            if owners and owner not in owners:
                print("Repo " + name + " with owner " + owner + " not backed up!")
                continue

            print("Backing up repo " + name)
            owner_path = os.path.join(path, owner)
            mkdir(owner_path)
            mirror(name, clone_url, owner_path, user["login"], token)

def backupBitBucket(repo, backupDir):
    user = repo["user"]
    workspace = repo["workspace"]
    token = repo["token"]
    path = os.path.expanduser(repo["directory"])
    path = os.path.join(backupDir, path)
    print("Backing up from Bitbucket:")
    if mkdir(path):
        print("Created directory {0}".format(path), file=sys.stderr)

    url = "https://api.bitbucket.org/2.0/repositories/" + workspace + "?pagelen=100"

    response = requests.get(url, auth=(user, token))

    repos = json.loads(response.text)
    for repo in repos["values"]:
        name = check_name(repo["name"])
        links = repo["links"]
        html = links["html"]
        clone_url = html["href"]
        backup_path = os.path.join(path, name)
        print("Backing up repo " + name)
        mkdir(backup_path)
        mirror(name, clone_url, backup_path, user, token)

def main():
    print("Backing up git repositories")

    configFile = os.getenv('CONFIG_FILE')
    backupDir = os.getenv('BACKUP_DIR')

    with open(configFile, "rb") as f:
        config = json.loads(f.read())

    repos = config["repositories"]
    try:
        repeatTime = int(config["repeat"])
    except:
        repeatTime = 0

    while(True):
        for repo in repos:
            type = repo["type"]
            if (type == "github"):
                backupGitHub(repo, backupDir)
            if (type == "bitbucket"):
                backupBitBucket(repo, backupDir)
        if (repeatTime == 0):
            exit()
        print("Will repeat backup in " + str(repeatTime) + " minutes")
        time.sleep(repeatTime * 60)



if __name__ == "__main__":
    main()
