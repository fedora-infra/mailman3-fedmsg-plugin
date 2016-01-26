# -*- coding: utf-8 -*-
# This file is part of fedmsg.
# Copyright (C) 2012 Red Hat, Inc.
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Ralph Bean <rbean@redhat.com>
#

""" Publish notifications about mails to the fedmsg bus.

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

"""

from zope.interface import implementer
from mailman.interfaces.archiver import IArchiver

import socket
import fedmsg
import fedmsg.config


implementer(IArchiver)
class Archiver(object):
    """ A mailman 3 archiver that forwards messages to the fedmsg bus. """

    name = "fedmsg"

    keys = [
        "archived-at",
        "delivered-to",
        "from",
        "cc",
        "to",
        "in-reply-to",
        "message-id",
        "subject",
        "x-message-id-hash",
        "references",
        "x-mailman-rule-hits",
        "x-mailman-rule-misses",
        "user-agent",
    ]

    def __init__(self):
        if not getattr(getattr(fedmsg, '__local', None), '__context', None):
            hostname = socket.gethostname().split('.')[0]
            fedmsg.init(name="mailman.%s" % hostname)
        self.config = fedmsg.config.load_config()


    def archive_message(self, mlist, msg):
        """Send the message to the "archiver".

        In our case, we just publish it to the fedmsg bus.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        """

        if mlist.list_name in self.config.get('mailman.excluded_lists', []):
            return

        # Here, by `str` we mean `unicode`.  We're python3 only!
        format = lambda value: value and str(value)
        msg_metadata = dict([(k, format(msg.get(k))) for k in self.keys])
        lst_metadata = dict(list_name=mlist.list_name)

        fedmsg.publish(topic='receive', modname='mailman',
                       msg=dict(msg=msg_metadata, mlist=lst_metadata))

    def list_url(self, mlist):
        """ This doesn't make sense for fedmsg.
        But we must implement for IArchiver.
        """
        return None

    def permalink(self, mlist, msg):
        """ This doesn't make sense for fedmsg.
        But we must implement for IArchiver.
        """
        return None
