# SPDX-FileCopyrightText: 2024 Contributors to the Fedora Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""Publish notifications about mails to the fedora-messaging bus.

See the README file for installation instructions.
"""

import email
import logging
import sys
import typing

import backoff
from fedora_messaging import api
from fedora_messaging.config import conf as fm_conf
from fedora_messaging.exceptions import ConnectionException, PublishTimeout
from mailman.interfaces.archiver import IArchiver
from mailman3_fedmsg_plugin_schemas import MessageV1
from zope.interface import implementer

_log = logging.getLogger("mailman.archiver")


def retry_handler(details):
    message = details["args"][0]
    _log.warning(
        "Publishing %r to %r failed. Retrying. %s",
        message.message_id,
        message.topic,
        sys.exc_info()[0].__name__,
    )


def giveup_handler(details):
    message = details["args"][0]
    _log.error(
        "Publishing %r to %r failed. Giving up. %s",
        message.message_id,
        message.topic,
        sys.exc_info()[0].__name__,
    )


@backoff.on_exception(
    backoff.expo,
    (ConnectionException, PublishTimeout),
    max_tries=3,
    on_backoff=retry_handler,
    on_giveup=giveup_handler,
    raise_on_giveup=False,
    logger=None,
)
def safe_publish(msg: api.Message):
    api.publish(msg)


def _to_string(value):
    return str(value) if value else None


@implementer(IArchiver)
class Archiver:
    """A mailman 3 archiver that forwards messages to the Fedora Messaging bus."""

    name = "fedmsg"

    message_headers: typing.ClassVar = [
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

    mlist_props: typing.ClassVar = [
        "list_name",
        "mail_host",
        "fqdn_listname",
        "list_id",
        "display_name",
    ]

    def __init__(self):
        self._config = fm_conf["consumer_config"]

    def list_url(self, mlist):
        """This doesn't make sense for fedora-messaging.
        But we must implement for IArchiver.
        """
        return None

    def permalink(self, mlist, msg):
        """This doesn't make sense for fedora-messaging.
        But we must implement for IArchiver.
        """
        return None

    def archive_message(self, mlist, msg):
        """Send the message to the "archiver".

        In our case, we just publish it to the fedmsg bus.

        :param mlist: The IMailingList object.
        :param msg: The message object.
        """

        if mlist.list_id in self._config.get("excluded_lists", []):
            return

        message = self._make_message(mlist, msg)
        _log.debug("Publishing %r to %r", message.message_id, message.topic)
        safe_publish(message)

    def _make_message(self, mlist, msg):
        msg_metadata = dict([(k, _to_string(msg.get(k))) for k in self.message_headers if k in msg])
        msg_metadata["recipients"] = self._get_recipients(msg)
        lst_metadata = dict([(prop, getattr(mlist, prop)) for prop in self.mlist_props])
        return MessageV1(
            body=dict(
                msg=msg_metadata,
                mlist=lst_metadata,
                url=self._get_url(msg),
                usernames=self._get_usernames(mlist, msg),
                sender_username=self._get_username(self._get_address_from_header(msg, "from")),
            ),
        )

    def _get_url(self, msg):
        archived_at = msg.get("archived-at")
        if archived_at:
            archived_at = archived_at.lstrip("<").rstrip(">")
        if not archived_at:
            return None
        if archived_at.startswith("http"):
            return archived_at
        base_url = self._config.get("archive_base_url")
        if not base_url:
            return None
        return base_url + archived_at

    def _get_usernames(self, mlist, msg):
        # We also include people that were explicitely added to CC or the To header.
        usernames = []
        for header in ("from", "to", "cc"):
            address = self._get_address_from_header(msg, header)
            if address == mlist.fqdn_listname:
                continue
            username = self._get_username(address)
            if username is not None:
                usernames.append(username)
        return usernames

    def _get_address_from_header(self, msg, header_name):
        value = msg.get(header_name)
        if value is None:
            return None
        address = email.utils.parseaddr(value.strip())[1]
        if not address:
            return None
        return address

    def _get_username(self, address):
        if not address:
            return None
        # TODO: make a FASJSON call?
        if any(address.endswith(f"@{domain}") for domain in self._config.get("owned_domains", [])):
            return address.split("@", 1)[0]
        else:
            return None

    def _get_recipients(self, msg):
        """The email's To and CC headers."""
        recipients = []
        for header in ("to", "cc"):
            address = self._get_address_from_header(msg, header)
            if not address:
                continue
            recipients.append(address)
        return recipients
