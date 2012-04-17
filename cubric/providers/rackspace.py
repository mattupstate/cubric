
import sys
import time

from fabric.api import env
from fabric.colors import green, yellow, red

from cubric.utils import get_or_prompt, get_password_from_console


def create_server():
    print(green("Creating Rackspace server..."))

    try:
        from cloudservers import CloudServers
        from cloudservers.exceptions import NotFound
    except ImportError:
        raise Exception("python-cloudservers libray required "
        				"for creating servers with Rackspace")

    cs = CloudServers(
    	get_or_prompt('rackspace_username', 'Username'),
    	get_or_prompt('rackspace_apikey', 'API Key'))

    image = cs.images.find(
    	id=int(get_or_prompt('rackspace_image', 'Server Image ID')))
    
    flavor = cs.flavors.find(
    	id=int(get_or_prompt('rackspace_flavor', 'Server Flavor ID')))

    server = cs.servers.create(
    	get_or_prompt('rackspace_servername', 'Server Name'), 
    	image=image, 
    	flavor=flavor)
    
    while True:
        while True:
            try:
                server = cs.servers.find(id=server.id)
                break;
            except NotFound:
                print(yellow('Waiting for new server'))
                time.sleep(10)
                pass

        if server.status != 'ACTIVE':
            print(yellow("Server status: %s" % server.status))
            time.sleep(10)
            continue
        break

    print(green("Server status: %s" % server.status))
    print(green("Update the server password:"))

    env.user = 'root'
    env.password = get_password_from_console()
    server.update(password=env.password)

    time.sleep(10)

    public_ip = server.addresses['public'][0]

    print(green("Instance state: %s" % server.status))
    print(green("Public IP: %s" % public_ip))
    
    return public_ip