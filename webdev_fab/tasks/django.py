from fabric.context_managers import settings, hide
from fabric.contrib import django
from fabric.contrib.files import append, exists, cd, lcd
from fabric.decorators import task
from fabric.operations import local, get, put, run, sudo
from fabric.state import env
from fabric.tasks import execute

from webdev_fab.tasks import *
from webdev_fab.tasks.python import (setup_virtualenv, recompile_py,
                                     install_reqs)
from webdev_fab.tasks.postgresql import (drop_db, create_db, upload_db,
                                         download_db)
from webdev_fab.utils import generate_django_secret_key

__all__ = ['deploy', 'local_to_remote', 'remote_to_local', 'provision',
           'manage', 'restart_project', 'set_local_setting', 'set_secret_key',
           'add_cronjobs', 'upload_uploads', 'download_uploads']


@task
def upload_uploads(cleanup=True):
    """Replace remote media/uploads directory with local one.

    Remove tarball on a remote host if 'cleanup' is True.
    """
    local('/bin/tar -C {}/media -c uploads > uploads.tar'.format(env.project))
    tarball = put('uploads.tar')[0]
    local('/bin/rm uploads.tar')
    with cd('project/{}/media'.format(env.project)):
        run('/bin/rm -rf uploads')
        run('/bin/tar -xf {}'.format(tarball))
        if cleanup:
            run('/bin/rm {}'.format(tarball))


@task
def download_uploads(replace=False, cleanup=True):
    """Download remote media/uploads directory.

    Replace local directory if 'replace' is True, remove downloaded
    tarball afterwards if 'cleanup' is also True.

    """
    run('/bin/tar -C project/{}/media -c uploads > uploads.tar'.format(
        env.project))
    tarball = get('uploads.tar'.format(env.project), '%(host)s-%(path)s')[0]
    run('/bin/rm uploads.tar'.format(env.project))
    if not replace:
        return
    local('/bin/rm -rf {}/media/uploads'.format(env.project))
    local('/bin/tar -C {0}/media -xf {1}'.format(env.project, tarball))
    if cleanup:
        local('/bin/rm {}'.format(tarball))


@task
def add_cronjobs():
    """Add cronjobs from project/cron files.

    Files matching "*.cron" in the cron directory must be valid crontab files.
    """
    if not exists('project/cron'):
        return
    with cd('project/cron'):
        run('cat *.cron > crontab.new')
        run("sed -i '/# DJANGOPROJ$/!s/$/ # DJANGOPROJ/g' crontab.new")
        user = env.user
        with hide('running', 'stdout'):
            cron_dir = run('pwd')
        with cd(cron_dir), settings(hide('warnings'), user=env.poweruser,
                                    warn_only=True):
            sudo('crontab -l -u {0} | grep -v "# DJANGOPROJ$" '
                 '>> crontab.new'.format(user))
            sudo('crontab crontab.new -u {0}'.format(user))
        run('rm crontab.new')


@task
def set_local_setting(name, value, backup=False):
    """Set name=value in settings/_local.py"""
    with cd('project/{}/settings'.format(env.project)),\
            settings(warn_only=True):
        if not exists('_local.py'):
            run('touch _local.py')
            run('chmod 600 _local.py')
        elif backup:
            run('sed -i s"|^\s*{0}\s*=\s*|#{0} = |" _local.py'.format(name))
        append('_local.py', "{0} = {1}".format(name, value))


@task
def set_secret_key():
    """Set random SECRET_KEY in settings/_local.py"""
    execute(set_local_setting, "SECRET_KEY",
            "'{}'".format(generate_django_secret_key()), backup=True)


@task
def restart_project(graceful=False):
    """Restart Django instance.

    Kill the uWSGI process, assuming it was stared by supervisor, which should
    respawn it.

    """
    if graceful:
        signal = 'SIGHUP'
    else:
        signal = 'SIGINT'
    with settings(hide('warnings'), warn_only=True):
        run('kill -{0} `cat project/tmp/uwsgi.pid`'.format(signal))


@task
def manage(command):
    """Run arbitrary Django management command."""
    with cd('project'):
        run('python manage.py {0}'.format(command))


@task
def provision():
    """
    Create system/db users, database, upload puplic key, setup virtualenv.
    """
    # TODO
    # create configs: nginx, uwsgi
    execute(create_user)
    execute(create_db)
    execute(upload_local_public_key, use_poweruser=True)
    execute(generate_keypair)
    execute(show_public_key)
    execute(setup_virtualenv)


@task
def deploy(syncdb=True, requirements=True, code=True, essential=False,
           permissions=True, upgrade=False):
    """Deploy a project, doing all the required magick.

    Fetch from env.repo (remember to add deployment key to the repository,
    see generate_keypair/show_public_key tasks). On the host:
    checkout env.branch in non-bare repository, update requirements, run
    essential management commands, restart project.

    """
    if essential:
        syncdb = requirements = code = permissions = False

    if not exists('project'):
        run('git clone -q {} project'.format(env.repo))
        execute(set_secret_key)

    with cd('project'):
        run('git checkout -q {}'.format(env.branch))
        run('git pull -q --ff-only origin {}'.format(env.branch))
        with cd('{}/settings'.format(env.project)):
            if not exists('__init__.py'):
                run('ln -s {}.py __init__.py'.format(env.type))
        run('/bin/mkdir -p {}/media/{{static,uploads}}'.format(env.project))
        run('/bin/mkdir -p tmp')
        run('/bin/chmod 750 tmp')
        with settings(hide('stdout', 'running')):
            projdir = run('pwd', )
        if (permissions and
            not run('[ $(stat -c %G tmp) == {} ]'.format(
                    env.webserver_group), warn_only=True).succeeded):
            with settings(user=env.poweruser), cd(projdir):
                sudo('/bin/chgrp {} tmp'.format(env.webserver_group))

    if requirements:
        execute(install_reqs, upgrade=upgrade)

    execute(manage, 'collectstatic --noinput --verbosity=0')

    if syncdb:
        execute(manage, 'syncdb --migrate')

    if code:
        execute(recompile_py, ignore_errors=True)
        # brutally restart uWSGI master process to reread available packages
        execute(restart_project)
    else:
        # Gracefully restart uWSGI master process to reset:
        #  template.loaders.cached.Loader cache
        #  local memory cache for CachedStaticFilesStorage
        execute(restart_project, graceful=True)


@task
def local_to_remote():
    """Deploy, replace remote db and uploaded media with local copies."""
    execute(upload_db)
    execute(deploy, syncdb=False)
    execute(upload_uploads)


@task
def remote_to_local():
    """Replace local db and uploaded media with remote copies.

    Use 'download_uploads' and 'download_db' tasks with required arguments for
    more control.

    """
    execute(download_db, restore=True, cleanup=True)
    execute(download_uploads, replace=True)
