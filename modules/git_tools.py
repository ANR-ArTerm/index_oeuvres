import subprocess
from datetime import datetime

def git_pull():
    """
    Exécute un 'git pull' et renvoie (success: bool, output: str).
    """
    try:
        result = subprocess.run(
            ["git", "pull"],
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


import subprocess

def git_commit_and_push(message: str, branch: str = "main"):
    """
    Exécute la séquence complète :
    - git add .
    - git commit -m "<message>"
    - git pull --rebase
    - git push

    Renvoie (success: bool, output: str).
    """
    try:
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)

        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            check=True,
            capture_output=True,
            text=True
        )

        pull_result = subprocess.run(
            ["git", "pull", "--rebase", "origin", branch],
            check=True,
            capture_output=True,
            text=True
        )

        push_result = subprocess.run(
            ["git", "push", "origin", branch],
            check=True,
            capture_output=True,
            text=True
        )

        output = "\n".join([
            commit_result.stdout,
            pull_result.stdout,
            push_result.stdout
        ])
        return True, output

    except subprocess.CalledProcessError as e:
        # Renvoie stdout + stderr pour plus d’infos
        return False, f"{e.stdout}\n{e.stderr}"