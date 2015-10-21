Opsview external Ansible inventory script
=========================================

 DESCRIPTION:
--------------
    Python script retrieves servers list and ssh ports from Opsview vis APIs, and it supports 3 kinds of output formats:
      1. Ansible dynamic inventory (http://docs.ansible.com/ansible/intro_dynamic_inventory.html).
      2. OpenSSH config file (~/.ssh/config).
      3. Pure JSON for any other purposes.

 NOTES:
--------------
    1. You can pass arguments to this script or edit defaults values directly in it (may use ini file later),
       but if you are going to use it with Ansible, you have to edit defaults values, because Ansible
       pass two arguments only to inventory script which are "--list" or "--host".
    2. You have to make "Host Template" contains all servers in your Opsview, and get its "ID" (that appears in template URL).
    3. By default this script depends two Opsview "Service Checks" which are "SSH" and "SSH-Non-Active".
    4. Unlike "SSH" check, "SSH-Non-Active" is not a default check, and you need to add it to your Opsview,
       see the documentation of this script and how this dummy check works.
    5. Default output for this script is SSH config file syntax.
    6. This script tested with Opsview Core 3.20131016.0.

    For more information about Opsview APIs please check:
      - https://docs.opsview.com/doku.php?id=opsview-core:restapi

 SYNTAX:
--------------
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
      --list                    Print output as Ansible dynamic inventory format.
      --host HOST               Ansible option to get information for specific host.
```

 VERSION:
--------------
    v0.1 - October 2015.

 BY:
--------------
    Ahmed M. AbouZaid (http://tech.aabouzaid.com/) - Under GPL v2.0 or later.

 TODO:
--------------
    Adding more details in documentation, rewrite some parts, make some enhancements and classes.
