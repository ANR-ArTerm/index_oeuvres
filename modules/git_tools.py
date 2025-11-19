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


def git_commit_and_push(message: str):
    """
    Exécute la séquence complète :
    - git add .
    - git commit -m "<message>"
    - git push

    Renvoie (success: bool, output: str).
    """
    try:
        # git add .
        subprocess.run(["git", "add", "."], check=True)

        # git commit -m "<message>"
        subprocess.run(
            ["git", "commit", "-m", message],
            check=True,
            capture_output=True,
            text=True
        )

        # git push
        result = subprocess.run(
            ["git", "push"],
            check=True,
            capture_output=True,
            text=True
        )

        return True, result.stdout

    except subprocess.CalledProcessError as e:
        return False, str(e)