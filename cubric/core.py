
from fabric.api import env

from cubric.utils import get_server, get_provider, get_app_context


class Server(object):

    initializer = None
    sudo_user = None

    def __init__(self, sudo_user):
        self.sudo_user = sudo_user

    def configure(self, configurator):
        if not callable(configurator):
            raise Exception('configurator is not a callable')
        return configurator()

    def initialize(self):
        if not self.initializer:
            raise Exception('Server does not specify a initializer')
        return self.configure(self.initializer)

    def reboot(self):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()


class ApplicationContext(object):

    def __init__(self, name=None, user=None, environment=None):
        self.name = name
        self.user = user
        self.environment = environment

    def restart(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def upload_release(self):
        raise NotImplementedError()

    def upload_config(self):
        raise NotImplementedError()

    def link_config(self):
        raise NotImplementedError()


class server(object):
    def __init__(self, user=None):
        self.user = user
        self.old_user = None
        self.old_server = None

    def __enter__(self):
        self.old_user = env.get('user', None)
        self.old_server = env.get('server', None)
        env.server = get_server()
        env.user = self.user or env.user
        return env.server

    def __exit__(self, *args, **kwargs):
        env.user = self.old_user
        env.server = self.old_server


class app_context(object):
    def __init__(self):
        self.old_ctx = None

    def __enter__(self):
        self.old_ctx = env.get('app_context', None)
        env.app_context = get_app_context()
        return  env.app_context

    def __exit__(self, *args, **kwargs):
        env.app_context = self.old_ctx


class provider(object):
    def __init__(self):
        self.old_provider = None

    def __enter__(self):
        self.old_provider = env.get('provider', None)
        env.provider = get_provider()
        return  env.provider

    def __exit__(self, *args, **kwargs):
        env.provider = self.old_provider
