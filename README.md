Some Fabric tasks for Django projects
=====================================

Generic tasks
-------------

### provision

Runs the followintg sub-tasks, which can be run separately:

 * create_user
 * create_db
 * upload_local_public_key
 * generate_keypair
 * show_public_key
 * setup_virtualenv

Django tasks
------------

### deploy

Deploy a project, doing all the required magick.

### local_to_remote

Deploy, replace remote db and uploaded media with local copies.

### manage:commandname

Run arbitrary Django management command.

### restart_project

Kill Django instance, which should be restarted by supervisor process.

### set_local_setting:name,value,backup

Set settings/_local.py value.

General rules
-------------

 * host should be accessible through SSH
 * local Git repository's remote `origin` with branch `master` is used
   by default to update the project code on the host
 * we use PostgreSQL with admin user `postgres`, db name defaults to `env.user`
 * remote user is in the main group of the same name
 * `env.poweruser` has full sudo privileges, defaults to the running user's
   name and is used to create user, db, chown operations, etc
 * `env.type` holds the host type and defaults to `production` and is used for
   choosing Django settings and PIP requirements files

Remote host package requirements
--------------------------------

 * Basic development packages (gcc, autotools, openssl, zlib, etc)
 * Some supervisor program to run Django WSGI process
 * PostgreSQL server (matching local version, if you want to use custom
   dump files)
 * Git, SVN, Mercurial, cURL

Optional requirements
---------------------

 * local db access is granted to `env.user` (~/.pgpass might help)
 * remote db access is granted to the system user with the same name

Example usage
--------------

### Per-project Fabfile.py

    from fabric.api import env
    from webdev_fab import set_project_defaults
    from webdev_fab.tasks import *
    from webdev_fab.tasks.django import *

    env.user = 'projname'

    # A shortcut to set 'db', 'db_user', 'group' and 'project' values equal
    # to 'user', which are required for this tasks to function
    set_project_defaults(env.user)

    # Everything else is optional

    # Default list of hosts to run tasks on
    if not env.hosts:
        env.hosts = ['somehost.yourteam.com:2222']

    # Fabric can can utilize some ~/.ssh/config shortcuts
    env.use_ssh_config = True

    # The user with full sudo privileges, defaults to the user running 'fab'
    env.poweruser = 'privilegedusername'

    # A group to own project/tmp directory with fcgi socket/pid files, defaults
    # to 'nginx'
    env.webserver_group = 'www-data'

### Essential command line examples

    fab -l
    fab provision
    fab local_to_remote
    git commit -a -m "Some changes" && git push && fab deploy

Links
-----

This project is used in a custom [django basic project template](https://github.com/mikek/django-basic-project-template)
and Chef/knife-solo based [django-kitchen](https://github.com/mikek/django-kitchen).
