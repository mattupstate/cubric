
from __future__ import with_statement

from fabric.api import env, task

from cubric.core import provider, server, app_context
from cubric.utils import get_callable


@task
def create_server(initialize=True):
    """Create a server"""
    with provider() as p:
        host_string = p.create_server()
        if initialize:
            env.host_string = host_string
            initialize_server()


@task
def initialize_server():
    """Initializer the sever"""
    with server() as s:
        s.initialize()


@task
def configure_server():
    """Configure the sever"""
    configurator = get_callable('server_configurator', 'Configurator')
    with server() as s:
        s.configure(configurator)


@task
def reboot_server():
    """Reboot the sever"""
    with server() as s:
        s.reboot()


@task
def restart_server():
    """Restart the sever"""
    with server() as s:
        s.restart()


@task
def start_server():
    """Start the sever"""
    with server() as s:
        s.start()


@task
def stop_server():
    """Stop the sever"""
    with server() as s:
        s.stop()


@task
def restart_app():
    """Restart the application"""
    with app_context() as c:
        c.restart()


@task
def start_app():
    """Start the applicaiton"""
    with app_context() as c:
        c.start()


@task
def stop_app():
    """Stop the application"""
    with app_context() as c:
        c.stop()


@task
def create_app_context():
    """Create an app context"""
    with app_context() as c:
        c.create()


@task
def upload_release():
    """Upload a new app release"""
    with app_context() as c:
        c.upload_app()


@task
def upload_config():
    """Upload a new app config"""
    with app_context() as c:
        c.upload_config()


@task
def link_config():
    """Symlink necessary config files"""
    with app_context() as c:
        c.link_config()


@task
def deploy():
    """Full deploy (upload_release, upload_config, link_config, restart_app)"""
    with app_context() as c:
        c.deploy()
