Publish notifications about mails to the fedmsg bus.

Enable this by adding the following to your mailman.cfg file::

    [archiver.fedmsg]
    # The class implementing the IArchiver interface.
    class: mailman3_fedmsg_plugin.Archiver
    enable: yes

You can exclude certain lists from fedmsg publication by
adding them to a 'mailman.excluded_lists' list in /etc/fedmsg.d/::

    config = {
        'mailman.excluded_lists': ['bugzilla', 'commits'],
    }
