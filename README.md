Opsview external Ansible inventory script
=========================================

ToC
--------------
  * [Description.](#description)
  * [Why?](#why)
  * [Approach.](#approach)
  * [Requirements.](#requirements)
  * [How it works?](#how-it-works)
  * [Configuration.](#configuration)
  * [Syntax.](#syntax)
  * [Output example.](#output-example)
  * [About.](#about)
  * [To-do.](#to-do)

<p align="center">
<img src="http://4.bp.blogspot.com/-QcmQyNjPXmk/Vi08WC6heuI/AAAAAAAACIc/ofSuOGGhj-M/s1600/Ansible_Ospview_OpenSSH_JSON_logos.png" width="320">
</p>

Description.
--------------
Python script retrieves servers list and ssh ports from Opsview via APIs, and it supports 3 kinds of output formats:
  1. Ansible [dynamic inventory](http://docs.ansible.com/ansible/intro_dynamic_inventory.html).
  2. OpenSSH config file ("~/.ssh/config").
  3. Pure JSON for any other purposes.

For more information you can check this post:<br />
http://tech.aabouzaid.com/2015/10/opsview-as-dynamic-inventory-for-ansible-python.html

Why?
--------------
I needed to one place has all servers information, but I didn't find anything simple and modern for [Ansible](http://ansible.com/) except [Ansible Tower](http://www.ansible.com/tower), which is great but too advanced and more than is required. Eventually I found we already almost add all servers to monitoring server (mostly based on [Nagios](https://www.nagios.org/) either [Icinga](https://www.icinga.org/) or [Opsview](http://opsview.com/)). I didn't like idea of getting data from configuration or database directly, so I decided to make it with APIs.

But I need a reliable way to get these data, I want the solution has the following:
* Work remotely, that's why I preferred APIs in the first place.
*  Don't make a lot of load on server, and don't make many huge queries! Think in terms of lots of servers on your monitoring server.
* Can be selective, so I have control over servers, for example some devices working through SNMP not SSH like most of routers and switches.


Approach.
--------------
In fact, you can easily get a just list of servers from Opsview with minimum work needed, but as mentioned before, I just want one place has all servers with SSH port (**thus most of extra work will be to get SSH port!**).

So the information I need is: 
* Server Group.
* Server Name.
* IP/Hostname.
* SSH port.

But I need a reliable way to get these data, I want the solution has the following:
* Work remotely, that's why I preferred APIs in the first place.
* Don't make a lot of load on server, and don't make many huge queries! Think in terms of lots of servers on your monitoring server.
* Can be selective, so I have control over servers, for example some devices working through SNMP not SSH like most of routers and switches.


Requirements.
--------------
I tried to make it simple and generalize the solution, reduced number of dependences, and use default settings as possible, also minimize modifications and pre-configuration.

So, what do you need to use this script with Opsview? (I will assume you are familiar with Opsview and its terminologies).

* A "Host Template" has all servers you want them to be in your inventory. You can call this template anything, we just need its ID.
* A new dummy check script on Opsview server (we will take a look on it after a bit).
* A "Service Check" using the dummy script we added to main Opsview server.
* An Opsview user with Administrator privileges.


How it works?
--------------
Once you made the necessary dependences, here is simply how this script work:
* Call Opsview API to get content of the "Host Template".
* Store content of "Host Template" which are server name and server URL in Opsview.
* Query for every URL in the list to get "Server Group" and "IP/Hostname".
* Make a query for active SSH check, and if it return ssh port number it will stop here.
* If active check didn't return ssh port number, then it will check passive check which always will return a number.

Now we have all the data we need which are again: Server Group, Server Name, IP/Hostname, and SSH port. We need just format it in one of 3 formats: OpenSSH config, Anisble JSON, or pure JSON. 


Configuration.
--------------
After this long introduction, let's go ahead and make some configuration in Opsview for the script.

* Create a "Host Template" in your Opsview contains all servers you need to be in your inventory, and get its "ID" (that appears in template URL). So, create a new Host Template and add whatever servers you want to it (or just clone existing one):
```
Settings > Basic > Host Template > Create new Host Template
```
<p align="center">
<img src="http://2.bp.blogspot.com/-6RQCBZylPYQ/Vi3fNdduhpI/AAAAAAAACIw/SQbCbQMNbik/s1600/Add_dummy_SSH_check.png" width="320">
</p>

Just hover the mouse over Template name and you will see the ID:
> https://YOUR_OPSVIEW_URL/admin/hosttemplate/edit/**71**

* Second step, create a dummy ssh check, which is just a bash script prints any arguments passed to it. Unlike "SSH" check, "SSH-Non-Active" is not a default check, and you need to add it to your Opsview.
    Connect to Opsview server though SSH, and create "check_ssh_dummy" file with following commands:

```
cat << EOS > /usr/local/nagios/libexec/check_ssh_dummy
#! /bin/bash
echo $*
exit 0
EOS

chown nagios: /usr/local/nagios/libexec/check_ssh_dummy

chmod ug+x /usr/local/nagios/libexec/check_ssh_dummy
```

* Now create a new "Server Check" (or just clone existing one) and name it "SSH-Non-Active":
```
Settings > Advanced > Service Checks > Create new Service Check
```

<p align="center">
<img src="http://4.bp.blogspot.com/-EIpwN68MxRE/Viundnh306I/AAAAAAAACH4/NUXuGqdV5sk/s1600/AllServers_Template.png" width="320">
</p>

** As you can see here, you actually can add this check to multiple templates, so if you have many servers with different ssh ports, you actually can set the port to bunch of server with few clicks, or set the port individually for any server (That's why I did choose make a new check not using attribute, which is hard to edit it with massive servers). **

* Create a new Role (Opsview user) with Administrator privileges:<br />
  Don't forget to reload Opsview to read new configuration. We almost done and ready to use the script now! But let's take a look on how it actually works?!
```
Settings > Basic > Contacts > Create new Contact
```

* Now, you have all required configuration,  all what you need is just edit those configuration inside the script or inside the ini file. You have following values to edit:
```
[Defaults]
; Opsview URL, Role (Opsview user), and its Password.
; Security level required for user is "Administrator".
"Opsview URL": ""
"Opsview User": ""
"Opsview Password": ""

; SSH user that will be printed.
"SSH User": "root"

; The ID of template that has all servers in Opsview.
; You need to find ID number in your Opsview.
"Template ID": ""

; Name of real SSH check.
"Active check name": "SSH"

; Name of dummy SSH check.
"Passive check name": "SSH-Non-Active"
```


Syntax.
--------------
You can pass some arguments to this script or edit defaults values directly inside the script OR use ini file, but if you are going to use it with Ansible, you have to edit defaults values inside the script OR using ini file, because Ansible pass two arguments only to inventory script which are "--list" or "--host".

You need at least one of 3 arguments: "--json", "--ssh", or "--list" (or the human readable argument --ansible), all other variables stored in the script.

```
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
      --host HOST               Ansible option to get information for specific host.
```

Output example.
--------------
I will assume you already edited the values inside the script, and just need to select output format.

**Ansible dynamic inventory (--ansible or --list):**
> ./opsview-ansible-inventory.py --ansible --user xuser

```
{
    "Group1": {
        "hosts": [
            "Server1", 
            "Server2"
        ]
    }, 
    "Group2": {
        "hosts": [
            "Server3", 
            "Server4",
        ]
    }, 
    "_meta": {
        "hostvars": {
            "Server1": {
                "Hostname": "10.0.0.1", 
                "Port": "22", 
                "User": "xuser"
            }, 
            "Server2": {
                "Hostname": "10.0.0.2", 
                "Port": "22", 
                "User": "xuser"
            }, 
            "Server3": {
                "Hostname": "10.0.0.3", 
                "Port": "22", 
                "User": "xuser"
            }, 
            "Server4": {
                "Hostname": "10.0.0.4", 
                "Port": "22", 
                "User": "xuser"
            }
        }
    }
}
```

**SSH (--ssh):**
> ./opsview-ansible-inventory.py --ssh --user xuser

```
##############################
# Groupname Group1

Host Server1
  Hostname 10.0.0.1
  Port 22
  User xuser

Host Server2
  Hostname 10.0.0.2
  Port 22
  User xuser

##############################
# Groupname Group2

Host Server3
  Hostname 10.0.0.3
  Port 22
  User xuser

Host Server4
  Hostname 10.0.0.4
  Port 22
  User xuser
```

**Pure JSON (--json):**
> ./opsview-ansible-inventory.py --json --user xuser

```
{
    "Group1": {
        "Server1": {
            "Hostname": "10.0.0.1", 
            "Port": "22", 
            "User": "xuser"
        }, 
        "Server2": {
            "Hostname": "10.0.0.2", 
            "Port": "22", 
            "User": "xuser"
        }
    }, 
    "Group2": {
        "Server3": {
            "Hostname": "10.0.0.3", 
            "Port": "22", 
            "User": "xuser"
        }, 
        "Server4": {
            "Hostname": "10.0.0.4", 
            "Port": "22", 
            "User": "xuser"
        }
    }
}
```


About.
--------------
* **By:** Ahmed M. AbouZaid [http://tech.aabouzaid.com/](http://tech.aabouzaid.com/).
* **Version:** v0.1 - October 2015.
* **License:**  GPL v2.0 or later.


To-do.
--------------
Adding more details in documentation, rewrite some parts, make some enhancements and classes.
