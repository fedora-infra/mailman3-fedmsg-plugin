# SPDX-FileCopyrightText: 2024 Contributors to the Fedora Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later

"""This module contains the Mailman message schema."""

import email
import typing

from fedora_messaging import message, schema_utils


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
            tmpl = "{user} wrote {subject!r} to the {listname} list"
        listname = self.list_address.split("@", 1)[0]
        sender_username = self.body.get("sender_username")
        if sender_username:
            from_user = sender_username
        else:
            from_user = "someone"
        return tmpl.format(listname=listname, user=from_user, subject=self.subject)

    @property
    def sender(self):
        """The email's From header."""
        raise NotImplementedError

    @property
    def recipients(self):
        """The email's To header."""
        raise NotImplementedError

    @property
    def date(self):
        """The email's Date header."""
        raise NotImplementedError

    @property
    def list_id(self):
        """The email's List-Id header."""
        raise NotImplementedError

    @property
    def list_address(self):
        """The mailinglist's address."""
        raise NotImplementedError

    @property
    def subject(self):
        """The email's subject."""
        raise NotImplementedError

    @property
    def message_id(self):
        """The email's Message-Id header."""
        raise NotImplementedError

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
        return self.body.get("url")

    @property
    def app_icon(self):
        """An URL to the icon of the application that generated the message."""
        return "https://apps.fedoraproject.org/img/icons/hyperkitty.png"

    @property
    def usernames(self):
        """List of users affected by the action that generated this message."""
        return self.body.get("usernames", [])

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

    body_schema: typing.ClassVar = {
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
                    "recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["from", "date"],
            },
            "url": {
                "type": "string",
                "description": "Where the message is archived",
            },
            "usernames": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of usernames related to this message",
            },
            "sender_username": {"type": ["string", "null"]},
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
        return self.body["msg"].get("recipients", [])

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
        return self.body["msg"].get("references") or self.body["msg"].get("in-reply-to")
