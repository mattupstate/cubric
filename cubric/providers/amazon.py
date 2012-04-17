
import sys
import time

from fabric.api import prompt
from fabric.colors import green, yellow

from cubric.utils import get_or_prompt, get_or_prompt_list


def create_server():
    """Creates an EC2 Server"""

    try:
        import boto
    except ImportError:
        sys.exit("boto library required for creating servers with Amazon.")

    print(green("Creating EC2 server"))

    conn = boto.connect_ec2(
        get_or_prompt('ec2_key', 'API Key'),
        get_or_prompt('ec2_secret', 'API Secret'))
    
    reservation = conn.run_instances(
        get_or_prompt(
            'ec2_ami', 'AMI ID', 'ami-fd589594'),
        instance_type=get_or_prompt(
            'ec2_instancetype', 'Instance Type', 't1.micro'),
        key_name=get_or_prompt(
            'ec2_keypair', 'Key Pair'),
        security_groups=get_or_prompt_list(
            'ec2_secgroups', 'Security Groups'))
    
    instance = reservation.instances[0]
    
    time.sleep(3)

    tag = get_or_prompt('ec2_tag', 'Instance Tag (blank for none)', '').strip()

    if len(tag) > 0:
        conn.create_tags([instance.id], {"Name": tag})
    
    while instance.state != u'running':
        print(yellow("Instance state: %s" % instance.state))
        time.sleep(10)
        instance.update()

    print(green("Instance state: %s" % instance.state))
    print(green("Public dns: %s" % instance.public_dns_name))
    print(green("Waiting 30 seconds for server to boot"))
    
    time.sleep(30)

    return instance.public_dns_name