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
# Authors:  Ian Kitembe <ianedwin@outlook.com>
#

""" Publish notifications about mails to the fedmsg bus.

Enable this by adding the following to your mailman.cfg file::

    [archiver.fedmsg]
    # The class implementing the IArchiver interface.
    class: mailman3_fedmsg_plugin.Archiver
    enable: yes

You can exclude certain lists from fedora messaging publication by
adding them to a 'excluded_lists' list in /etc/fedora-messaging/config.toml::

    [consumer_config]
    excluded_lists = ['bugzilla', 'commits'],
"""

from backoff import expo, on_exception
from zope.interface import implementer
from mailman.interfaces.archiver import IArchiver
from fedora_messaging.message import Message
from fedora_messaging.api import publish
from fedora_messaging.exceptions import ConnectionException, PublishTimeout
from fedora_messaging.config import conf


@on_exception(
    expo,
    (ConnectionException, PublishTimeout),
    max_tries=3,
)
def safe_publish(msg: Message):
    publish(msg)


@implementer(IArchiver)
class Archiver(object):
    """
    A mailman 3 archiver that forwards messages to the fedmsg bus.
    """

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

    def archive_message(self, mlist, msg):
        """
        Send the message to the "archiver".

        In our case, we just publish it to the fedmsg bus.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        """

        if mlist.list_name in conf["consumer_config"].get("excluded_lists", []):
            return

        def _format(value):
            return str(value) if value else value

        msg_metadata = {key: _format(getattr(msg, key, None)) for key in self.keys}
        lst_metadata = {
            "list_name": mlist.list_name,
            "mail_host": mlist.mail_host,
            "fqdn_listname": mlist.fqdn_listname,
            "list_id": mlist.list_id,
            "display_name": mlist.display_name,
        }
        body = dict(msg=msg_metadata, mlist=lst_metadata)
        fm_msg = Message(body=body, topic="mailman.receive")
        safe_publish(fm_msg)

    def list_url(self, mlist):
        """
        This doesn't make sense for fedmsg.
        But we must implement for IArchiver.
        """
        return None

    def permalink(self, mlist, msg):
        """
        This doesn't make sense for fedmsg.
        But we must implement for IArchiver.
        """
        return None
