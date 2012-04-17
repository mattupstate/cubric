

from __future__ import with_statement

import os

from cuisine import *
from fabric.api import env
from fabric.colors import *
from fabric.utils import puts
from fabric.context_managers import cd, settings, prefix
from fabric.contrib.console import confirm

from cubric.core import Server as BaseServer, ApplicationContext, app_context, server
from cubric.utils import app_bundle


class Initializer(object):
    def __init__(self):
        with mode_sudo():
            # Ensure an admin group
            group_ensure('admin')

            # Create the ubuntu user if it does not exist
            if not user_check('ubuntu'):
                user_create('ubuntu', home='/home/ubuntu')

            # Ensure the ubuntu user is in the admin group
            group_user_ensure('admin', 'ubuntu')

            # Ensure the sudoers file allows admin group users
            # and ubuntu user has password-less sudo access
            puts(green("Updating /etc/sudoers"))
            file_update(
                '/etc/sudoers', 
                lambda _: text_ensure_line(_,
                    '%admin ALL=(ALL) ALL',
                    'ubuntu  ALL=(ALL) NOPASSWD:ALL'
            ))

            # Perhaps the admin will want to add their public key to the 
            # ubuntu user for password-less SSH access
            if confirm("Do you want to add your public key to the ubuntu "
                       "user's authorized_keys file?"):
                puts(green("Adding your public key to ubuntu user"))
                ssh_authorize('ubuntu', file_local_read('~/.ssh/id_rsa.pub'))
            
            # Ubuntu doesn't always have the latest nginx build
            # so here the nginx ubuntu repository is added
            puts(green('Updating repository info for nginx'))
            file_update(
                '/etc/apt/sources.list', 
                lambda _: text_ensure_line(_,
                    'deb http://nginx.org/packages/ubuntu/ lucid nginx',
                    'deb-src http://nginx.org/packages/ubuntu/ lucid nginx'
            ))

            # Add the signing key so nginx builds can be downloaded
            puts(green('Adding singing key for nginx'))
            keys = run('apt-key list')

            if not 'nginx' in keys:
                run('wget http://nginx.org/keys/nginx_signing.key')
                run('apt-key add nginx_signing.key')
            
            # Update apt
            run('apt-get update -qq')
            
            # Ensure the following packages are installed
            for p in ['build-essential', 
                      'libmysqlclient-dev', 
                      'libxml2-dev', 
                      'libjpeg62-dev', 
                      'python-dev', 
                      'python-setuptools', 
                      'python-mysqldb', 
                      'python-pip',
                      'mysql-client', 
                      'git-core', 
                      'nginx']:
                puts(green('Installing: ' + p))
                package_ensure(p)
            
            # Link some .so files. This is a little house keeping step
            # in case a library such as PIL is installed
            puts(green('Linking libraries'))
            for l in [('/usr/lib/x86_64-linux-gnu/libfreetype.so', 
                           '/usr/lib/libfreetype.so'),
                      ('/usr/lib/x86_64-linux-gnu/libz.so', 
                           '/usr/lib/libz.so'),
                      ('/usr/lib/x86_64-linux-gnu/libjpeg.so', 
                           '/usr/lib/libjpeg.so')]:
                file_link(l[0], l[1])
            
            # Install some Python libraries
            for p in ['virtualenv', 
                      'virtualenvwrapper',
                      'supervisor',
                      'uwsgi']:
                puts(green('Installing: ' + p))
                run('pip install ' + p)
            
            # Configure nginx and supervisor
            puts(green('Configuring supervisor and nginx'))
            
            tdir = os.path.dirname(__file__)
            for f in [('/etc/supervisord.conf', 'supervisord.conf.tmpl'),
                      ('/etc/nginx/nginx.conf', 'nginx.conf.tmpl'),
                      ('/etc/init.d/supervisor', 'supervisor.tmpl')]:
                fn = f[0]
                contents = file_local_read(os.path.join(tdir, 'templates', f[1]))
                if not file_exists(fn):
                    file_write(fn, contents)
                else:
                    file_update(fn, lambda _:contents)

            puts(green('Create supervisor config folder'))
            dir_ensure('/etc/supervisor')

            # Make sure supervisor runs on startup
            run('chmod +x /etc/init.d/supervisor')
            run('update-rc.d supervisor defaults')

            # Start supervisor
            run('/etc/init.d/supervisor start')
        
        puts(green('Server setup complete!'))
        puts(green('Add sites to nginx by linking configuration files in /etc/nginx/conf.d'))
        puts(green('Add uWSGI processes to supervisor by linking configuration files in /etc/supervisor'))


class Server(BaseServer):
    """Default Ubuntu server configured with nginx, uWSGI and supervisor"""

    initializer = Initializer

    def reboot(self):
        puts(green('Rebooting server'))
        sudo('reboot')

    def restart(self):
        puts(green('Restarting server'))
        for c in ['nginx', 'supervisor']:
            sudo('/etc/init.d/%s restart' % c, pty=False)

    def start(self):
        puts(green('Starting server'))
        for c in ['nginx', 'supervisor']:
            sudo('/etc/init.d/%s start' % c, pty=False)

    def stop(self):
        puts(green('Stoping server'))
        for c in ['nginx', 'supervisor']:
            sudo('/etc/init.d/%s stop' % c, pty=False)


class WsgiApplicationContext(ApplicationContext):

    def __init__(self, name='default', user='ubuntu', 
                 wsgi_file='wsgi.py', wsgi_callable='application',
                 nginx_template=None, supervisor_template=None):
        super(WsgiApplicationContext, self).__init__(name, user)
        self.wsgi_file = wsgi_file
        self.wsgi_callable = wsgi_callable
        self.virtualenv = '/home/%s/.virtualenv/%s' % (self.user, self.name)
        self.root_dir = '/home/%s/sites/%s' % (self.user, self.name)
        self.releases_dir = self.root_dir + '/releases'
        self.src_dir = self.releases_dir + '/current'
        self.shared_dir = self.root_dir + '/shared'
        self.etc_dir = self.root_dir + '/etc'
        self.log_dir = self.root_dir + '/log'
        self.run_dir = self.root_dir + '/run'
        self.nginx_template = nginx_template or \
            'etc/%s/nginx.conf.tmpl' % env.environment
        self.supervisor_template = supervisor_template or \
            'etc/%s/supervisor.conf.tmpl' % env.environment

    def create(self):
        """Create an application context on the server"""

        puts(green('Creating app context'))
        tdir = os.path.dirname(__file__)

        # Ensure the app context user exists
        user_ensure(self.user, home='/home/' + self.user)
        dir_ensure('/home/%s/.ssh' % self.user)

        t = '/home/%s/.ssh/authorized_keys'
        app_authorized_keys = t % env.user
        ctx_authorized_keys = t % self.user

        # Ensure the app user has the same authorized_keys as the admin user
        if file_exists(app_authorized_keys) and \
           not file_exists(ctx_authorized_keys):
            sudo('cp %s %s' % (app_authorized_keys, ctx_authorized_keys))
            file_attribs(ctx_authorized_keys, mode=755, 
                         owner=self.user, group=self.user)
        
        # Actions to be performed with the app context user
        with settings(user=self.user):
            # Make sure the dot files exist
            # This is mostly necessary for virtualenvwrapper to work properly
            for f in ['bashrc', 'bash_profile', 'profile']:
                lfn = os.path.join(tdir, 'templates', '%s.tmpl' % f)
                contents = file_local_read(lfn) % self.__dict__
                rfn = '/home/%s/.%s' % (self.user, f)
                file_ensure(rfn, owner=self.user, group=self.user)
                file_update(rfn, lambda _:contents)
            
            # Make sure the sites folder exists
            dir_ensure('/home/%s/sites' % self.user)
            
            # Make sure the app's required folders exist
            for d in [self.root_dir, self.releases_dir, self.etc_dir, 
                      self.log_dir, self.run_dir, self.shared_dir]:
                dir_ensure(d)

    def upload_release(self):
        """Upload an application bundle to the server for a given context"""
        with settings(user=self.user):
            with app_bundle():
                local_bundle = env.local_bundle
                env.bundle = '/tmp/' + os.path.basename(local_bundle)
                file_upload(env.bundle, local_bundle)

            # Extract the bundle into a release folder
            current_release_link = self.releases_dir + '/current'
            previous_release_link = self.releases_dir + '/previous'
            release_dir = self.releases_dir + '/' + env.release

            dir_ensure(release_dir)
            with cd(release_dir):
                run('tar -xvf ' + env.bundle)

            # Delete the remote bundle
            run('rm ' + env.bundle)

            # Remove previous release link
            if file_exists(previous_release_link):
                run('rm ' + previous_release_link)

            # Move current to previous
            if file_exists(current_release_link):
                run('mv %s %s' % (current_release_link, previous_release_link))

            # Link the current release
            file_link(release_dir, self.releases_dir + "/current")
        
            # Recreate virtualenv
            for c in ['rm', 'mk']:
                run(c + 'virtualenv ' + self.name)

            # Install app dependencies
            with cd(current_release_link):
                with prefix('workon ' + self.name):
                    run('pip install -r requirements.txt')

    def upload_config(self):
        with settings(user=self.user):
            # Render nginx and supervisor configuration files
            for c in [(self.nginx_template, 'nginx'), 
                      (self.supervisor_template, 'supervisor')]:
                
                fn = '%s/%s.conf' % (self.etc_dir, c[1])
                contents = file_local_read(c[0]) % self.__dict__
                
                if file_exists(fn):
                    file_update(fn, lambda _:contents)
                else:
                    file_write(fn, contents)

    def link_config(self):
        with mode_sudo():
            for c in [('/etc/nginx/conf.d', 'nginx'), 
                      ('/etc/supervisor', 'supervisor')]:
                source = '%s/%s.conf' % (self.etc_dir, c[1])
                destination = '%s/%s.conf' % (c[0], self.name)

                if file_exists(destination):
                    run('rm ' + destination)
                
                file_link(source, destination)

    def start(self):
        with server() as s:
            s.start()

    def stop(self):
        with server() as s:
            s.stop()

    def restart(self):
        with server() as s:
            s.restart()

    def deploy(self):
        self.upload_release()
        self.upload_config()
        self.link_config()
        self.restart()