import random
import base64
import uuid
from fabric.operations import local
from fabric.context_managers import quiet


def generate_django_secret_key():
    return ''.join(
        [random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)")
         for i
         in range(50)])


def generate_tornado_cookie_secret():
    return base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)


def get_git_remote_url(remote_name='origin', url_type='fetch'):
    """Get remote url.

    Default remote='origin', url_type='fetch'. Return None if unable to find.

    """
    with quiet():
        remote = local(
            "git remote -v show | "
            "grep -E '^{}\s.+\({}\)$'".format(remote_name, url_type),
            capture=True)
        if remote.failed:
            return
        url = local("echo '{}' | awk '{{print $2}}'".format(remote),
                    capture=True)
    if url.succeeded:
        return url
