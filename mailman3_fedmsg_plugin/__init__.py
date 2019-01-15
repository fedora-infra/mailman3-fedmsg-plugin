# This file is part of mailman3-fedmsg-plugin.
#
# Copyright (C) 2018  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Lesser Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""Publish notifications about mails to the fedora-messaging bus.

See the README file for installation instructions.
"""

import logging

from zope.interface import implementer
from mailman.interfaces.archiver import IArchiver
from mailman.interfaces.configuration import MissingConfigurationFileError
from mailman.config import config
from mailman.config.config import external_configuration


from fedora_messaging import api
from fedora_messaging_schemas.mailman.schemas import MessageV1


_log = logging.getLogger("mailman.archiver")


def _to_string(value):
    return str(value) if value else None


@implementer(IArchiver)
class Archiver(object):
    """ A mailman 3 archiver that forwards messages to the fedmsg bus. """

    name = "fedmsg"

    message_headers = [
        "archived-at",
        "delivered-to",
        "date",
        "from",
        "cc",
        "to",
        "in-reply-to",
        "message-id",
        "subject",
        "message-id-hash",
        "x-message-id-hash",
        "references",
        "x-mailman-rule-hits",
        "x-mailman-rule-misses",
        "user-agent",
    ]

    mlist_props = ["list_name", "mail_host", "fqdn_listname", "list_id", "display_name"]

    def __init__(self):
        self._config = {"excluded_lists": []}
        self._load_config()

    def _load_config(self):
        try:
            archiver_config = external_configuration(
                config.archiver.fedora_messaging.configuration
            )
        except MissingConfigurationFileError:
            return
        self._config["excluded_lists"] = [
            name.strip()
            for name in archiver_config.get(
                "general", "excluded_lists", fallback=""
            ).split(",")
            if name.strip()
        ]

    def list_url(self, mlist):
        """ This doesn't make sense for fedora-messaging.
        But we must implement for IArchiver.
        """
        return None

    def permalink(self, mlist, msg):
        """ This doesn't make sense for fedora-messaging.
        But we must implement for IArchiver.
        """
        return None

    def archive_message(self, mlist, msg):
        """Send the message to the "archiver".

        In our case, we just publish it to the fedmsg bus.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        """

        if mlist.list_id in self._config["excluded_lists"]:
            return

        message = self._make_message(mlist, msg)
        self._send_to_amqp(message)

    def _make_message(self, mlist, msg):
        msg_metadata = dict([(k, _to_string(msg.get(k))) for k in self.message_headers if k in msg])
        lst_metadata = dict([(prop, getattr(mlist, prop)) for prop in self.mlist_props])
        return MessageV1(body=dict(msg=msg_metadata, mlist=lst_metadata))

    def _send_to_amqp(self, message):
        _log.debug("Publishing %r to %r", message.message_id, message.topic)
        try:
            api.publish(message)
        except Exception as e:
            _log.exception(
                'Publishing "%r" on topic "%r" failed (%r)',
                message.message_id,
                message.topic,
                e,
            )
