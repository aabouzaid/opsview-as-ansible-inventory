#!/usr/bin/python

"""
Opsview external Ansible inventory script
=========================================

 DESCRIPTION:
    Python script retrieves servers list and ssh ports from Opsview vis APIs, and it supports 3 kinds of output formats:
      1. Ansible dynamic inventory (http://docs.ansible.com/ansible/intro_dynamic_inventory.html).
      2. OpenSSH config file (~/.ssh/config).
      3. Pure JSON for any other purposes.

 NOTES:
    1. To using and and requirements, and pre-configuration please check the documentation of the script at its Github repository:
       https://github.com/AAbouZaid/opsview-as-ansible-inventory
    2. You can pass arguments to this script or edit defaults values directly in it (may use ini file later),
       but if you are going to use it Ansible dynamic inventory, you have to edit defaults values,
       because Ansible passes two arguments only to inventory script which are "--list" or "--host".
    3. You have to make "Host Template" contains all servers in your Opsview, and get its "ID" (that appears in template URL).
    4. By default this script depends two Opsview "Service Checks" which are "SSH" and "SSH-Non-Active".
    5. Unlike "SSH" check, "SSH-Non-Active" is not a default check, and you need to add it to your Opsview,
       see script documentation to see how it works.
    6. This script tested with Opsview Core 3.20131016.0.
    7. For more information about Opsview APIs please check:
       https://docs.opsview.com/doku.php?id=opsview-core:restapi


 SYNTAX:
    usage: opsview-ansible-inventory.py [-h]
                                        [--template-id TEMPLATE_ID]
                                        [--active-check-name ACTIVE_CHECK_NAME]
                                        [--passive-check-name PASSIVE_CHECK_NAME]
                                        [--user USER]
                                        [--json] [--ssh] [--list]
                                        [--host HOST]

    optional arguments:
      -h, --help                show this help message and exit
      --template-id TEMPLATE_ID
                                The ID of "Host Template" that has all servers in your Opsview.
      --active-check-name ACTIVE_CHECK_NAME
                                Name of active "Service Check" as in your Opsview. Default is "SSH".
      --passive-check-name PASSIVE_CHECK_NAME
                                Name of passive "Service Check" as in your Opsview. Default is "SSH-Non-Active".
      --user USER               Name of SSH user that will be printed as output. Default is "root".
      --json                    Print output as JSON format.
      --ssh                     Print output as OpenSSH config file format.
      --ansible, --list         Print output as Ansible dynamic inventory format.
      --ansible-static          Print output as Ansible static inventory format.
      --host HOST               Ansible option to get information for specific host.

 VERSION:
    v0.1 - October 2015.

 BY:
    Ahmed M. AbouZaid (http://tech.aabouzaid.com/) - Under GPL v2.0 or later.

 TODO:
    Adding more details in documentation, rewrite some parts, make some enhancements and classes.
"""

import re
import sys
import json
import urllib
import urllib2
import argparse

#-----------------------------------
# Default values.
Defaults = {
    # Opsview URL, Role (Opsview user), and its Password.
    # Security level required for user is "Administrator".
    "Opsview URL": "",
    "Opsview User": "",
    "Opsview Password": "",

    # SSH user that will be printed.
    "SSH User": "root",

    # The ID of template that has all servers in Opsview.
    # You need to find ID number in your Opsview.
    "Template ID": "",

    # Name of real SSH check.
    "Active check name": "SSH",

    # Name of dummy SSH check.
    "Passive check name": "SSH-Non-Active"
}

# Use ini file -if you want!- instead hardcoded values inside the script.
ini_file = "./opsview-ansible-inventory.ini"
# If there is any empty value in Defaults dictionary inside the script, it will use .ini file.
ini_config = '' in Defaults.values()

if ini_config == True:
    # Check if ini file exists.
    import os
    if os.path.isfile(ini_file) is False:
        print "Please make sure %s exists in the script's directory." % (ini_file)
        sys.exit(1)

    # Import ConfigParser module and use .ini file.
    import ConfigParser
    config = ConfigParser.ConfigParser()
    # To make ConfigParser case sensitive. 
    config.optionxform = str
    config.read(ini_file)
    # Use configuration inside .ini file. 
    Defaults = dict(config.items('Defaults'))

# Check if default values are provided.
if '' in Defaults.values():
    print "You have to edit default values (in the ini file or inside the script)."
    sys.exit(1)


#-----------------------------------
# Script options.
parser = argparse.ArgumentParser()
parser.add_argument("--template-id", help="The ID of \"Host Template\" that has all servers in your Opsview.", type=str)
parser.add_argument("--active-check-name", help="Set active \"Service Check\" name as in your Opsview. Default is \"SSH\".")
parser.add_argument("--passive-check-name", help="Set passive \"Service Check\" name as in your Opsview. Default is \"SSH-Non-Active\".")
parser.add_argument("--user", help="SSH user. Default is \"root\".")
parser.add_argument("--json", help="Print output as JSON format.", action="store_true")
parser.add_argument("--ssh",  help="Print output as OpenSSH config file format.", action="store_true")
parser.add_argument("--list", "--ansible", help="Print output as Ansible dynamic inventory syntax.", action="store_true")
parser.add_argument("--ansible-static", help="Print output as Ansible static inventory syntax.", action="store_true")
parser.add_argument("--host", help="Ansible option to get information for specific host.")
args = parser.parse_args()


#-----------------------------------
# Check variables.

# Check if no arguments provided.
if args.json == args.ssh == args.list == args.ansible_static == False:
    parser.print_help()
    sys.exit(1)

# The Host Template that has all servers in Opsview, you have to check the id in your Opsview.
if not args.template_id and not Defaults["Template ID"]:
    print "You have to edit default values inside th script or use --template-id [ID]."
elif args.template_id:
    host_template_id = args.template_id
else:
    host_template_id = Defaults["Template ID"]

# Set ssh user, if not set, the user will be "root".
if args.user == None:
    user = Defaults["SSH User"]
else:
    user = args.user

# Set active "Service Check" name as in your Opsview, default is "SSH".
if args.active_check_name == None:
    active_check_name = Defaults["Active check name"]
    active_port = ""
else:
    active_check_name = args.active_check_name

# Set passive "Service Check" name as in your Opsview, default is "SSH-Non-Active".
if args.passive_check_name == None:
    passive_check_name = Defaults["Passive check name"]
    passive_port = ""
else:
    passive_check_name = args.passive_check_name


#-----------------------------------
# Communicate with Opsview REST APIs.
# I got this section form this post:
# http://deli-systems.blogspot.com.eg/2011/12/using-opsview-api-via-python.html

# Credentials.
opsview_url = Defaults["Opsview URL"]
opsview_user = Defaults["Opsview User"]
opsview_password = Defaults["Opsview Password"]

# Cookies.
ops_cookies = urllib2.HTTPCookieProcessor()
ops_opener = urllib2.build_opener(ops_cookies)

ops = ops_opener.open(
    urllib2.Request(opsview_url + "/rest/login",
        urllib.urlencode(dict({'username': opsview_user,'password': opsview_password}))
    )
)

response_text = ops.read()
response = eval(response_text)

# Evaluate the response.
if not response:
    print("Cannot evaluate %s" % response_text)
    sys.exit()

if "token" in response:
    ops_token = response["token"]
else:
    print("Opsview authentication FAILED")
    sys.exit(1)

# Fetch servers list form Host Template.
headers = {
    "Content-Type": "application/json",
    "X-Opsview-Username": opsview_user,
    "X-Opsview-Token": ops_token,
}


#-----------------------------------
# Get main data: Group name, Host, Hostname, Port, and User.

# Get the data from Opsview REST API in JSON format.
def get_url_data(api_url, url_type):
    if url_type == "template":
        url = opsview_url + api_url + host_template_id
    elif url_type in ["host", "service"]:
        url = opsview_url + api_url
    request = urllib2.Request(url, None, headers)
    return json.loads(ops_opener.open(request).read())

# Reformat output as Ansible dynamic inventory or just pure JSON. 
groups = dict()
def hostname_port_user():
    hostname_port_user = {
        "Hostname": hostname,
        "Port": port,
        "User": user
    }
    return hostname_port_user

# Get the data from "config" section in rest API. More info about "config" in Opsview API:
# http://docs.opsview.com/doku.php?id=opsview-core:restapi:config

all_servers_template = get_url_data("/rest/config/hosttemplate/", "template")

# Check if "--host" is present, so will retrieve that host only not the full list.
if args.host:
    for server in all_servers_template["object"]["hosts"]:
        if server["name"] == args.host:
            servers_list = [server]
else:
    servers_list = all_servers_template["object"]["hosts"]

# 
for server in servers_list:
    server_json_data = get_url_data(server["ref"], "host")

    # Set main variables for every host in list like Group name, Host, Hostname, Port, and User.
    group_name = host = hostname = port = ""
    group_name = server_json_data["object"]["hostgroup"]["name"]
    host = server_json_data["object"]["name"].lower()
    hostname = server_json_data["object"]["ip"]

    # We need to use "status" section to get SSH port, which is not in "config" secion.
    for servicename in [active_check_name, passive_check_name]:
        url = "/rest/status/service/?servicename=%s&hostname=%s" % (servicename, host)
        service_check_data = get_url_data(url, "service")

        # Check if can get port number from active ssh check.
        if servicename == active_check_name:
            try:
                service_output = service_check_data["list"][0]["services"][0]["output"]
            except IndexError:
                active_port = ""
            else:
                try:
                    active_port = re.findall('(?<=port )\d+', service_output)[0]
                except IndexError:
                    active_port = ""

        # Get port number from passive ssh check (the dummy check).
        elif servicename == passive_check_name:
            passive_port = service_check_data["list"][0]["services"][0]["output"]

        # This will give an error if active or passive check not found. 
        else:
            print "This host (%s: %s) don't have %s or %s, please add it." % (host, hostname, active_check_name, passive_check_name)
            sys.exit(1)

    # Check if "active_port" variable has port in numbers only, I use regex because the number here is a "string" not an "integer".
    if re.findall('^\d+$', active_port):
        port = active_port
    else:
        port = passive_port


    #-----------------------------------
    # Format the output.

    # Ansible format.
    if args.list is True:
        if group_name not in groups.keys():
            groups[group_name] = {"hosts": [host]}
        elif "_meta" not in groups.keys():
            groups["_meta"] = {"hostvars": {}}
        else:
            # Add the host to hosts list, then add its variables to "_meta" dict.
            groups[group_name]["hosts"].append(host)
            groups["_meta"]["hostvars"].update({host: hostname_port_user()})

    # Ansible single host format.
    elif args.host:
        groups[group_name] = {"hosts": [host]}
        groups["_meta"] = {"hostvars": {host: hostname_port_user()}}

    # JSON format.
    else:
        if group_name not in groups.keys():
          # Add new group to groups dict.
          groups[group_name] = {}
          # Add the host to its group.
          groups[group_name].update({host: hostname_port_user()})
        else:
          # Add the host to its group.
          groups[group_name].update({host: hostname_port_user()})


#-----------------------------------
# Print the output.

# Pure JSON output.
if args.json is True:
    print json.dumps(groups, sort_keys=True, indent=4)

# Ansible dynamic inventory output.
elif args.list is True or args.host:
    print json.dumps(groups, sort_keys=True, indent=4) 

# Ansible static inventory output.
elif args.ansible_static:
    for group in groups.keys():
      print "\n[" + group.lower() + "]"

      for server in groups[group]:
        hostname = port = user = ""
        hostname = groups[group][server]["Hostname"]
        port = groups[group][server]["Port"]
        user = groups[group][server]["User"]
        print "%s ansible_ssh_host=%s ansible_ssh_port=%s ansible_ssh_user=%s" % (server, hostname, port, user)

# SSH Config syntax output.
elif args.ssh:
    indent_space = "\t".expandtabs(2)
    for group in groups.keys():
      print "#" * 30
      print "# Groupname " + group.capitalize() + "\n"

      for server in groups[group]:
        print "Host %s" % (server)
        print "%sHostname %s" % (indent_space, groups[group][server]["Hostname"])
        print "%sPort %s" % (indent_space, groups[group][server]["Port"])
        print "%sUser %s\n" % (indent_space, groups[group][server]["User"])
