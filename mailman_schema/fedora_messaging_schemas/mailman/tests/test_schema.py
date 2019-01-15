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

"""Unit tests for the message schemas."""
import unittest
import datetime

from jsonschema import ValidationError
from fedora_messaging_schemas.mailman import schemas


class MessageV1Tests(unittest.TestCase):
    """A set of unit tests to ensure the schema works as expected."""

    msg_class = schemas.MessageV1

    def setUp(self):
        self.minimal_message = {
            "mlist": {
                "list_name": "infrastructure",
                "mail_host": "lists.fedoraproject.org",
                "fqdn_listname": "infrastructure@lists.fedoraproject.org",
                "list_id": "infrastructure.lists.fedoraproject.org",
                "display_name": "Infrastructure list",
            },
            "msg": {
                "from": "JD <jd@example.com>",
                "to": "infrastructure@lists.fedoraproject.org",
                "date": "Mon, 20 Nov 1995 19:12:08 -0500",
            },
        }
        self.full_message = {
            "mlist": {
                "list_name": "infrastructure",
                "mail_host": "lists.fedoraproject.org",
                "fqdn_listname": "infrastructure@lists.fedoraproject.org",
                "list_id": "infrastructure.lists.fedoraproject.org",
                "display_name": "Infrastructure list",
            },
            "msg": {
                "archived-at": "<http://example.com/12345>",
                "delivered-to": "someone@example.com",
                "date": "Mon, 20 Nov 1995 19:12:08 -0500",
                "from": "Me <me@fedoraproject.org>",
                "cc": "them@fedoraproject.org",
                "to": "You <you@example.com>",
                "in-reply-to": "<abc-123@example.com",
                "message-id": "12345",
                "subject": "A sample email",
                "x-message-id-hash": "potatoes",
                "references": "<abc-123@example.com>",
                "x-mailman-rule-hits": "3",
                "x-mailman-rule-misses": "0",
                "user-agent": "L33t mailer",
            },
        }

    def test_minimal_message(self):
        """
        Assert the message schema validates a message with the minimal number
        of required fields.
        """
        message = self.msg_class(body=self.minimal_message)

        message.validate()

    def test_full_message(self):
        """Assert a message with all fields passes validation."""
        message = self.msg_class(body=self.full_message)

        message.validate()

    def test_missing_fields(self):
        """Assert an exception is actually raised on validation failure."""
        del self.minimal_message["msg"]["date"]
        message = self.msg_class(body=self.minimal_message)

        self.assertRaises(ValidationError, message.validate)

    def test_str(self):
        """Assert __str__ produces a human-readable message."""
        expected_str = (
            "From: me@fedoraproject.org\n"
            "Date: 1995-11-20 19:12:08-05:00\n"
            "List-Id: infrastructure.lists.fedoraproject.org\n"
            "Subject: A sample email\n"
        )
        message = self.msg_class(body=self.full_message)
        message.validate()
        self.assertEqual(expected_str, str(message))

    def test_summary(self):
        """Assert the summary matches the message subject."""
        message = self.msg_class(body=self.full_message)
        expected = "On the infrastructure list, me replied to 'A sample email'"
        self.assertEqual(expected, message.summary)

    def test_subject(self):
        """Assert the message provides a "subject" attribute."""
        message = self.msg_class(body=self.full_message)

        self.assertEqual("A sample email", message.subject)

    def test_url(self):
        """Assert the message provides a "url" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual("http://example.com/12345", message.url)

    def test_agent_avatar(self):
        """Assert the message provides a "agent_avatar" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual(
            "https://seccdn.libravatar.org/avatar/"
            "a69324d226d537ba9a9ece5742e9f25d"
            "?s=64&d=retro",
            message.agent_avatar,
        )

    def test_usernames(self):
        """Assert the message provides a "usernames" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual(["me", "them"], message.usernames)

    def test_packages(self):
        """Assert the message provides a "packages" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual([], message.packages)

    def test_sender(self):
        """Assert the message provides a "sender" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual("me@fedoraproject.org", message.sender)

    def test_recipients(self):
        """Assert the message provides a "sender" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual(
            ["you@example.com", "them@fedoraproject.org"], message.recipients
        )

    def test_date(self):
        """Assert the message provides a "date" attribute."""
        message = self.msg_class(body=self.full_message)
        # expected = datetime.datetime(1995, 11, 20, 19, 12, 8, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=68400)))
        expected = datetime.datetime(
            1995,
            11,
            20,
            19,
            12,
            8,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-5)),
        )
        self.assertEqual(expected, message.date)

    def test_list_id(self):
        """Assert the message provides a "list_id" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual("infrastructure.lists.fedoraproject.org", message.list_id)

    def test_list_address(self):
        """Assert the message provides a "list_address" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual("infrastructure@lists.fedoraproject.org", message.list_address)


class MessageV2Tests(MessageV1Tests):
    """A set of unit tests to ensure the schema works as expected."""

    msg_class = schemas.MessageV2

    def setUp(self):
        self.minimal_message = {
            "mailing_list": "infrastructure@lists.fedoraproject.org",
            "mailing_list_id": "infrastructure.lists.fedoraproject.org",
            "date": "Mon, 20 Nov 1995 19:12:08 -0500",
            "from": "JD <jd@example.com>",
            "to": ["infrastructure@lists.fedoraproject.org"],
        }
        self.full_message = {
            "mailing_list": "infrastructure@lists.fedoraproject.org",
            "mailing_list_id": "infrastructure.lists.fedoraproject.org",
            "delivered-to": "someone@example.com",
            "date": "Mon, 20 Nov 1995 19:12:08 -0500",
            "from": "Me <me@fedoraproject.org>",
            "cc": ["them@fedoraproject.org"],
            "to": ["you@example.com"],
            "x-mailman-rule-hits": "3",
            "x-mailman-rule-misses": "0",
            "x-message-id-hash": "potatoes",
            "references": ["<abc-123@example.com>"],
            "in-reply-to": ["<abc-123@example.com"],
            "message-id": "12345",
            "archived-at": "<http://example.com/12345>",
            "subject": "A sample email",
        }

    def test_missing_fields(self):
        """Assert an exception is actually raised on validation failure."""
        del self.minimal_message["date"]
        message = self.msg_class(body=self.minimal_message)

        self.assertRaises(ValidationError, message.validate)

    def test_url(self):
        """Assert the message provides a "url" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual("http://example.com/12345", message.url)

    def test_agent_avatar(self):
        """Assert the message provides a "agent_avatar" attribute."""
        message = self.msg_class(body=self.full_message)
        self.assertEqual(
            "https://seccdn.libravatar.org/avatar/"
            "a69324d226d537ba9a9ece5742e9f25d"
            "?s=64&d=retro",
            message.agent_avatar,
        )
