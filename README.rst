Publish notifications about mails to the fedmsg bus.

Enable this by adding the following to your mailman.cfg file::

    [archiver.fedora_messaging]
    # The class implementing the IArchiver interface.
    class: mailman3_fedmsg_plugin.Archiver
    enable: yes
    configuration: /etc/mailman3/fedora-messaging.cfg

You can exclude certain lists from publication by creating a configuration file
at ``/etc/mailman3/fedora-messaging.cfg`` (or any value that you use in the
``configuration`` key above) and setting the following content::

    [general]
    excluded_lists: bugzilla.lists.fedoraproject.org, commits.lists.fedoraproject.org

The values must be the list ID (dotted format) and they must be separated by
commas if you want to exclude multiple lists.
