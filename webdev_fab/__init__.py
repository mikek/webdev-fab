from fabric.state import env
from .utils import get_git_remote_url

env.setdefault('branch', 'master')
env.setdefault('repo', get_git_remote_url())
env.setdefault('type', 'production')
env.setdefault('poweruser', env.local_user)
env.setdefault('webserver_group', 'nginx')


# makes possible to use the same codebase with different db/system users
def set_project_defaults(value):
    env.setdefault('group', value)
    env.setdefault('project', value)
    env.setdefault('db', value)
    env.setdefault('dbuser', value)
