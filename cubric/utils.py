
import os
import re
import tempfile
import types
from importlib import import_module

from cuisine import run_local
from fabric.api import prompt, env, local


def get_or_prompt(key, message, default='', validate=None):
    if env.has_key(key):
        return env[key]
    return prompt(message + ":", key, default, validate)


def get_or_prompt_list(key, message, default='', validate=None, delim=' '):
    message = message + ' (Delimiter="' + delim + '")'
    rv = get_or_prompt(key, message, default, validate)
    rv = env[key] = [v.strip() for v in rv.split(delim)]
    return rv


def import_obj(import_name):
    parts = import_name.split('.')
    module = '.'.join(parts[:-1])
    obj = parts[-1]
    return getattr(import_module(module), obj)


def get_app_context_vars():
    rv = {}
    prefix = 'app_context_'
    for key, value in env:
        if key.startswith(prefix):
            rv[key.replate(prefix, '')] = value
    return rv


def get_obj_from_env(key, message, instantiate=False):
    if isinstance(get_or_prompt(key, message), basestring):
        env[key] = import_obj(env[key])
    if instantiate:
        env[key] = env[key](environment=env.environment,
                            **get_app_context_vars())
    return env[key]


def get_callable(key, message):
    obj = get_obj_from_env(key, message)
    if not callable(obj):
        raise Exception("%s is not a callable" % obj)
    return obj


def get_server():
    return get_obj_from_env('server', 'Server class name', True)


def get_app_context():
    return get_obj_from_env('app_context', 'App context class name', True)


def get_provider():
    provider_name = get_or_prompt('provider', 'Amazon or Rackspace?')
    return import_module('cubric.providers.' + provider_name.strip().lower())


def get_password_from_console():
        from getpass import getpass

        password = getpass('Password: ')

        if len(password) < 6:
            print(red('Password should be a minimum of 6 characters. Try again.'))
            get_sever_password()

        verify = getpass('Retype Password: ')

        if password == verify:
            return password

        print(red('Passwords did not match. Try again.'))
        get_password_from_console()


def render(obj):
    """Convienently render strings with the fabric context"""
    def get_v(v):
        return v % env if isinstance(v, basestring) else v

    if isinstance(obj, types.StringType):
        return obj % env
    elif isinstance(obj, types.TupleType) or isinstance(obj, types.ListType):
        rv = []
        for v in obj:
            rv.append(get_v(v))
    elif isinstance(obj, types.DictType):
        rv = {}
        for k, v in obj.items():
            rv[key] = get_v(v)

    return rv


class app_bundle(object):

    def __enter__(self):
        run_local('git submodule init && git submodule update')

        env.release = local(render('git rev-parse %(branch)s | cut -c 1-9'), capture=True)
        env.release = re.sub('[\r\n]', '', env.release)

        env.local_bundle = tempfile.mkstemp(suffix='.tar')[1]
        run_local(render('git archive --format=tar %(branch)s > %(local_bundle)s'))

    def __exit__(self, *args, **kwargs):
        os.unlink(env.local_bundle)
        env.local_bundle = None