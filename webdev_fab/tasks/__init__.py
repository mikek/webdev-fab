import os

from fabric.colors import yellow, red
from fabric.context_managers import settings, hide
from fabric.contrib.files import append, exists, cd
from fabric.decorators import task
from fabric.operations import local, run, sudo
from fabric.state import env


@task
def create_user():
    """Create system user/group with home directory"""
    user = env.user
    with settings(hide('running')):
        local('echo "Switching to power user \'{}\'"'.format(env.poweruser))
    with settings(user=env.poweruser, warn_only=True):
        with settings(hide('everything')):
            group_exists = run('getent group {}'.format(env.group)).succeeded
            user_extsts = run('getent passwd {}'.format(user)).succeeded
        if not group_exists:
            sudo('/usr/sbin/groupadd {}'.format(env.group))
        if not user_extsts:
            # home dir is created in this step, so do not remove it afterwards
            sudo('/usr/sbin/useradd -m -g {0} {1}'.format(env.group, user))
            sudo('/usr/bin/passwd {}'.format(user))


@task
def upload_local_public_key(use_poweruser=False,
                            local_pub_key_path='~/.ssh/id_rsa.pub'):
    """Append local SSH public key to remote ~/.ssh/authorized_keys.

    If use_poweruser is set, uses sudo (usefull in situation before the key is
    uploaded while other login methods being disabled). If your system has
    ssh-copy-id(1), you may try to use it instead of this Fabric task.

    """
    target_user = env.user
    target_home = '.'
    acting_user = env.user
    remote_run = run
    use_sudo = False

    if use_poweruser:
        use_sudo = True
        remote_run = sudo
        acting_user = env.poweruser
        # switch to power user to login and create key file
        # (we do not allow unprivileged user login with password)
        with settings(hide('everything'), user=acting_user, warn_only=True):
            target_home = run("getent passwd {}"
                              "|awk -F: '{{print $6}}'".format(target_user))
            if not exists(target_home):
                print(red("User's home directory does not exist"))
                return

    pubkey_path = os.path.expanduser(local_pub_key_path)
    if not os.path.exists(pubkey_path):
        print(red("Local public key not found: {}".format(pubkey_path)))
        return

    key = ' '.join(open(pubkey_path).read().strip().split(' ')[:2])
    with settings(user=acting_user), cd(target_home):
        remote_run('mkdir -p .ssh')
        # 'append' with use_sudo duplicates lines within 'cd'.
        # https://github.com/fabric/fabric/issues/703
        # Passing 'shell=True' to append() (which is supported in
        # Fabric 1.6) fixes this issue.
        append('.ssh/authorized_keys', key, partial=True, shell=True,
               use_sudo=use_sudo)
        remote_run('chmod 600 .ssh/authorized_keys')
        remote_run('chmod 700 .ssh')
        remote_run('chown -R {0}:{0} .ssh'.format(target_user))


@task
def generate_keypair(use_passphraze=False, key_path='~/.ssh/id_rsa',
                     overwrite=False):
    """Generate SSH keypair."""
    files = (key_path, '{}.pub'.format(key_path))
    for f in files:
        if exists(f):
            if overwrite:
                # Early removal can lead to missing keypair if this task will
                # not finish, but it is acceptable.
                run('rm -rf {}'.format(f))
            else:
                print(yellow("File already exists: {}".format(f)))
                return
    run('ssh-keygen -t rsa -b 2048 -f {} {}'.format(
        key_path, '' if use_passphraze else '-N ""'))


@task
def show_public_key(pub_key_path='~/.ssh/id_rsa.pub'):
    """Echo SSH public key."""
    run('cat {}'.format(pub_key_path))
