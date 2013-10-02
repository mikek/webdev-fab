from fabric.context_managers import settings, hide
from fabric.decorators import task
from fabric.operations import run
from fabric.contrib.files import append, exists, cd
from fabric.state import env


@task
def setup_virtualenv(path='~/.env'):
    """Create new virtualenv, activate it in ~/.profile"""
    if not exists(path):
        v = '1.10.1'
        tarball = 'virtualenv-' + v + '.tar.gz'
        run('curl --insecure '
            '-O https://pypi.python.org/packages/source/v/virtualenv/' +
            tarball)
        run('tar xvfz ' + tarball)
        with cd('virtualenv-' + v):
            run('python virtualenv.py {}'.format(path))
    append('.profile', 'export LANG=en_US.UTF8', partial=True)
    append('.profile', '. {}/bin/activate'.format(path), partial=True)


@task
def install_reqs(upgrade=False, requirements_file=None):
    """Install required packages into virtualenv.

    Default requirements_file is requirements/{env.type}.txt

    """
    if not requirements_file:
        requirements_file = 'requirements/{}.txt'.format(env.type)
    with cd('project'):
        run('pip -q install {0} -r {1}'.format('--upgrade' if upgrade else '',
                                               requirements_file))


@task
def recompile_py(ignore_errors=False):
    """Recompile all *.pyc files found in the project and it's virtual env."""
    top_dir = 'project/{}'.format(env.project)
    prune_dirs = ''
    # Exclude some django-specific directories with potentially
    # huge number of files.
    for d in ('media', 'static', 'templates'):
        prune_dirs = '{0} -path {1}/{2} -prune -o'.format(
            prune_dirs, top_dir, d)
    find_prefix = 'find {0} -mindepth 1 {1} -type f'.format(
        top_dir, prune_dirs)
    find_venv_prefix = ('find $VIRTUAL_ENV/src -name .git -a -type d -prune '
                        '-o -type f')
    with settings(hide('stdout'), warn_only=ignore_errors):
        for prefix in find_prefix, find_venv_prefix:
            run('{} -name "*.pyc" -print | xargs rm'.format(prefix))
            run('{} -name "*.py" -print | python -m compileall -i -'.format(
                prefix))
