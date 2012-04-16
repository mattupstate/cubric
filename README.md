# Cubric

Cubric allows you to easily create and configure servers for Python projects on Amazon EC2 or Rackspace Cloud Servers. With a small amount of configuration you can create servers and deploy applications with great ease! 

Cubric has been developed using two core concepts:

### Servers
Servers are, you guessed it, servers! Servers are initialized and/or configured to run one or more applications. They can be rebooted, restarted, stopped, etc.

### Application Contexts

An application context is a specification for an application. It's sort of the 'house' the app lives in. They are generally specific to a particular type of server and the server's configuration. They can be deployed, stopped, started, restarted, etc.

## Getting Started

### Installation

Install Cubric:
    pip install https://github.com/mattupstate/cubric/tarball/develop

#### EC2:

Install boto:

    $ pip install boto

Configure your Fabric environment in your fabfile or by using an rcfile by adding the following values:

    user = ubuntu
    key_filename = /path/to/keyfile
    #host_string = to be added later

    provider = amazon
    server = cubric.contrib.servers.ubuntu.default.Server

    ec2_key = your_ec2_key
    ec2_secret = your_ec2_secret
    ec2_ami = ami-fd589594
    ec2_keypair = keypair_name
    ec2_secgroups = security_group_name
    ec2_instancetype = t1.micro

#### Rackspace:

Install python-cloudservers:

    $ pip install python-cloudservers

Configure your Fabric environment in your fabfile or by using an rcfile by adding the following values:

    user = root
    password = your_custom_password
    #host_string = to be added later

    provider = rackspace
    server = cubric.contrib.servers.ubuntu.default.Server

    rackspace_username = your_username
    rackspace_apikey = your_api_key
    rackspace_servername = your_server_name
    rackspace_image = 112
    rackspace_flavor = 1

### Create a Server

Add the following to your fabfile:
    
    from cubric.tasks import *

See the list of tasks that are available by running:

    $ fab --list

Create the server:

    $ fab -c rcfile create_server

If you've already created your server through your respective management console, or if something fails during server setup, you can run setup by setting the value for `host_string` in your rcfile to your server's public DNS or IP address and running:

    $ fab -c rcfile initialize_server

After the server is finished being created you'll want to uncomment and modify the `host_string` value in your rcfile to perform any more operations on your new server.

### Create an Application Context

An application context is the 'environment' under which an application lives. Cubric is primarily developed for Python applications. More specifically WSGI applications that are run using nginx, uWSGI, and supervisor. To create and application context on the server, add the following value to your Fabric environment:

    app_context = cubric.contrib.servers.ubuntu.default.WsgiApplicationContext

Then create the context by running:

    $ fab -c rcfile create_app_context

Now you should be ready to deploy your application

### Deploy Your App

    $ fab -c rcfile deploy

