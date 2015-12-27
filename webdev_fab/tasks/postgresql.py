from fabric.context_managers import settings, hide
from fabric.contrib.files import cd
from fabric.decorators import task
from fabric.operations import local, get, put, run, sudo
from fabric.state import env
from fabric.tasks import execute


@task
def drop_db():
    """Delete database"""
    with settings(user=env.poweruser, warn_only=True):
        sudo('dropdb {0}'.format(env.db), user='postgres')


@task
def create_db():
    """Create database with a dedicated user as the owner"""
    with settings(user=env.poweruser):
        with settings(hide('everything'), warn_only=True):
            db_user_exists = sudo(
                "psql --quiet -c '\du' | awk '{{print $1}}'\
                | egrep '^{}$'".format(env.dbuser), user='postgres').succeeded
            db_exists = sudo(
                "psql --quiet --list --tuples-only | awk '{{print $1}}'\
                | egrep '^{}$'".format(env.db), user='postgres').succeeded
        if not db_user_exists:
            sudo('createuser -P -S -D -R -e {}'.format(env.dbuser),
                 user='postgres')
        if not db_exists:
            sudo('createdb --echo --encoding=UTF8 '
                 '--owner={} {}'.format(env.dbuser, env.db),
                 user='postgres')


@task
def upload_db(recreate=True):
    """Upload local database dump and restore on host.

    Drop and recreate the target database if 'recreate' argument is True.

    """
    local('pg_dump --clean -F custom '
          '-U {0} {1} > {1}.backup'.format(env.dbuser, env.db))
    put('{}.backup'.format(env.db), '.')
    if recreate:
        execute(drop_db)
        execute(create_db)
    with settings(hide('stdout', 'running')):
        homedir = run('pwd', )
    with settings(user=env.poweruser):
        with cd(homedir):
            sudo('pg_restore -d {0} {0}.backup'.format(env.db),
                 user='postgres')
    local('/bin/rm {}.backup'.format(env.db))


@task
def download_db(restore=False, cleanup=False, recreate=True):
    """Download remote database dump.

    Restore dump on local host if 'restore' is True.
    Drop and recreate the target database if 'recreate' is True, remove dump
    file afterwards if 'remove' is also True.

    """
    with settings(hide('stdout', 'running')):
        run('pg_dump --clean -F custom '
            '{0} > {0}.backup'.format(env.db))
    dump_file = get('{}.backup'.format(env.db), '%(host)s-%(path)s')[0]
    if not restore:
        return
    if recreate:
        with settings(warn_only=True):
            local('dropdb -U {0} {1}'.format(env.dbuser, env.db))
        local('createdb --echo --encoding=UTF8 '
              '-U postgres --owner={0} {1}'.format(env.dbuser, env.db))
    local('pg_restore -U postgres -d {1} {2}'.format(
          env.dbuser, env.db, dump_file))
    if cleanup:
        local('/bin/rm {}'.format(dump_file))
