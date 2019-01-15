# This file is part of fedora-messaging-mailman-schemas
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

"""This module contains the different versions of the Mailman message schema."""

import email

from fedora_messaging import message, schema_utils


def _get_addr_username(address):
    return address.split("@", 1)[0]


class BaseMessage(message.Message):
    """
    Super class that each schema version inherits from.
    """

    def __str__(self):
        """Return a complete human-readable representation of the message."""
        template = "From: {sender}\nDate: {date}\nList-Id: {listid}\nSubject: {subj}\n"
        return template.format(
            sender=self.sender,
            date=self.date,
            listid=self.list_id,
            subj=self.subject,
        )

    @property
    def summary(self):
        """Return a summary of the message."""
        if self._is_reply():
            tmpl = "On the {listname} list, {user} replied to {subject!r}"
        else:
            tmpl = "{user} wrote {subject!} to the {listname} list"
        listname = _get_addr_username(self.list_address)
        if self.sender.endswith("@fedoraproject.org"):
            from_user = _get_addr_username(self.sender)
        else:
            from_user = "someone"
        return tmpl.format(listname=listname, user=from_user, subject=self.subject)

    @property
    def sender(self):
        """The email's From header."""
        return 'Message did not implement "sender" property'

    @property
    def recipients(self):
        """The email's To header."""
        return ['Message did not implement "recipients" property']

    @property
    def date(self):
        """The email's Date header."""
        return 'Message did not implement "date" property'

    @property
    def list_id(self):
        """The email's List-Id header."""
        return 'Message did not implement "list_id" property'

    @property
    def list_address(self):
        """The mailinglist's address."""
        return 'Message did not implement "list_address" property'

    @property
    def subject(self):
        """The email's subject."""
        return 'Message did not implement "subject" property'

    @property
    def message_id(self):
        """The email's Message-Id header."""
        return 'Message did not implement "message_id" property'

    @property
    def agent_avatar(self):
        """An URL to the avatar of the user who caused the action."""
        return schema_utils.libravatar_url(email=self.sender)

    @property
    def url(self):
        """An URL to the email in HyperKitty

        Returns:
            str or None: A relevant URL.
        """
        base_url = "https://lists.fedoraproject.org/archives"
        archived_at = self._get_archived_at()
        if archived_at and archived_at.startswith("<"):
            archived_at = archived_at[1:]
        if archived_at and archived_at.endswith(">"):
            archived_at = archived_at[:-1]
        if archived_at and archived_at.startswith("http"):
            return archived_at
        elif archived_at:
            return base_url + archived_at
        else:
            return None

    @property
    def app_icon(self):
        """An URL to the icon of the application that generated the message."""
        return "https://apps.fedoraproject.org/img/icons/hyperkitty.png"

    @property
    def usernames(self):
        """List of users affected by the action that generated this message."""
        # We include people that were explicitely added to CC or the To header.
        usernames = []
        for address in [self.sender] + self.recipients:
            if address == self.list_address:
                continue
            if address.endswith("@fedoraproject.org"):
                usernames.append(_get_addr_username(address))
        return usernames

    @property
    def packages(self):
        """List of packages affected by the action that generated this message."""
        return []


class MessageV1(BaseMessage):
    """
    A sub-class of a Fedora message that defines a message schema for messages
    published by Mailman when it receives mail to send out.
    """

    topic = "mailman.receive"

    body_schema = {
        "id": "http://fedoraproject.org/message-schema/mailman#",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Schema for message sent to mailman",
        "type": "object",
        "properties": {
            "mlist": {
                "type": "object",
                "properties": {
                    "list_name": {
                        "type": "string",
                        "description": "The name of the mailing list (before the '@' sign)",
                    },
                    "mail_host": {
                        "type": "string",
                        "description": "The domain of the mailing list",
                    },
                    "fqdn_listname": {
                        "type": "string",
                        "description": "The FQDN of the mailing list",
                    },
                    "list_id": {
                        "type": "string",
                        "description": "The mailing list ID (dotted notation)",
                    },
                    "display_name": {"type": "string"},
                },
            },
            "msg": {
                "description": "An object representing the email",
                "type": "object",
                "properties": {
                    "archived-at": {"type": "string"},
                    "delivered-to": {"type": "string"},
                    "date": {"type": "string"},
                    "from": {"type": "string"},
                    "cc": {"type": "string"},
                    "to": {"type": "string"},
                    "in-reply-to": {"type": "string"},
                    "message-id": {"type": "string"},
                    "subject": {"type": "string"},
                    "message-id-hash": {"type": "string"},
                    "x-message-id-hash": {"type": "string"},
                    "references": {"type": "string"},
                    "x-mailman-rule-hits": {"type": "string"},
                    "x-mailman-rule-misses": {"type": "string"},
                    "user-agent": {"type": "string"},
                },
                "required": ["from", "date"],
            },
        },
        "required": ["mlist", "msg"],
    }

    @property
    def message_id(self):
        """The email's Message-Id header."""
        return self.body["msg"].get("message-id")

    @property
    def subject(self):
        """The email's subject."""
        return self.body["msg"].get("subject", "").replace("\n", " ")

    @property
    def sender(self):
        """The email's From header."""
        from_header = self.body["msg"]["from"]
        return email.utils.parseaddr(from_header)[1]

    @property
    def recipients(self):
        """The email's To and CC headers."""
        recipients = []
        for header in ("to", "cc"):
            try:
                value = self.body["msg"][header].strip()
            except KeyError:
                continue
            value = email.utils.parseaddr(value)[1]
            if value:
                recipients.append(value)
        return recipients

    @property
    def date(self):
        """The email's Date header."""
        return email.utils.parsedate_to_datetime(self.body["msg"].get("date", ""))

    @property
    def list_id(self):
        """The email's List-Id header."""
        return self.body["mlist"]["list_id"]

    @property
    def list_address(self):
        """The mailinglist's address."""
        return self.body["mlist"]["fqdn_listname"]

    def _is_reply(self):
        return self.body["msg"].get("references") or self.body["msg"].get('in-reply-to')

    def _get_archived_at(self):
        return self.body["msg"].get("archived-at")


class MessageV2(BaseMessage):
    """
    This is a revision from the MessageV1 schema which flattens the message
    structure into a single object, but is backwards compatible for any users
    that make use of the properties.
    """

    topic = "mailman.receive.v2"

    body_schema = {
        "id": "http://fedoraproject.org/message-schema/mailman#",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Schema for message sent to mailman",
        "type": "object",
        "required": ["mailing_list", "mailing_list_id", "from", "date"],
        "properties": {
            "mailing_list": {
                "type": "string",
                "description": "The full name of the mailing list",
            },
            "mailing_list_id": {
                "type": "string",
                "description": "The list ID (dotted notation)",
            },
            "delivered-to": {"type": "string"},
            "date": {"type": "string"},
            "from": {"type": "string"},
            "cc": {"type": "array"},
            "to": {"type": "array"},
            "x-mailman-rule-hits": {"type": "string"},
            "x-mailman-rule-misses": {"type": "string"},
            "message-id-hash": {"type": "string"},
            "x-message-id-hash": {"type": "string"},
            "references": {"type": "array"},
            "in-reply-to": {"type": "array"},
            "message-id": {"type": "string"},
            "archived-at": {"type": "string"},
            "subject": {"type": "string"},
        },
    }

    @property
    def message_id(self):
        """The email's Message-Id header."""
        return self.body.get("message-id")

    @property
    def subject(self):
        """The email's subject."""
        return self.body.get("subject", "").replace("\n", " ")

    @property
    def sender(self):
        """The email's From header."""
        from_header = self.body["from"]
        return email.utils.parseaddr(from_header)[1]

    @property
    def recipients(self):
        """The email's To and CC headers."""
        recipients = self.body["to"] + self.body.get("cc", [])
        return [addr[1] for addr in email.utils.getaddresses(recipients) if addr[1]]

    @property
    def date(self):
        """The email's Date header."""
        return email.utils.parsedate_to_datetime(self.body.get("date", ""))

    @property
    def list_id(self):
        """The email's List-Id header."""
        return self.body["mailing_list_id"]

    @property
    def list_address(self):
        """The mailinglist's address."""
        return self.body["mailing_list"]

    def _is_reply(self):
        return self.body.get("references") or self.body.get('in-reply-to')

    def _get_archived_at(self):
        return self.body.get("archived-at")
