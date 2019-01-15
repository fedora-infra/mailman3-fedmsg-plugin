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
#
# Author: Aurelien Bompard <abompard@fedoraproject.org>
#

# pylint: disable=protected-access,too-few-public-methods,no-self-use

import os
import tempfile
import shutil
from textwrap import dedent
from unittest import TestCase

from mock import patch
from mailman.config import config
from mailman.email.message import Message
from mailman.testing.layers import ConfigLayer

from mailman3_fedmsg_plugin import Archiver


class FakeDomain:
    """Fake a Mailman domain implementing the IDomain interface"""

    def __init__(self, domain):
        self.mail_host = domain


class FakeList:
    """Fake a Mailman list implementing the IMailingList interface"""

    def __init__(self, name):
        self.fqdn_listname = name
        self.list_id = name.replace("@", ".")
        self.list_name, self.mail_host = name.split("@", 1)
        self.domain = FakeDomain(self.mail_host)
        self.display_name = self.list_name.capitalize()


class ArchiverTestCase(TestCase):

    layer = ConfigLayer

    def setUp(self):
        # Set up a temporary directory for the archiver so that it's
        # easier to clean up.
        self._tempdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tempdir)
        config.push(
            "fedora_messaging",
            """
        [archiver.fedora_messaging]
        class: mailman3_fedmsg_plugin.Archiver
        enable: yes
        configuration: {tmpdir}/fedora-messaging.cfg
        """.format(
                tmpdir=self._tempdir
            ),
        )
        self.addCleanup(config.pop, "fedora_messaging")
        with open(os.path.join(self._tempdir, "fedora-messaging.cfg"), "w") as conf_h:
            conf_h.write(
                dedent(
                    """
            [general]
            excluded_lists: excluded.lists.example.com
            """
                )
            )
        # Create the archiver
        self.archiver = Archiver()
        self.mlist = FakeList("list@lists.example.com")
        # Patch fedora-messaging
        self.fm_patcher = patch("mailman3_fedmsg_plugin.api")
        self.fm = self.fm_patcher.start()

    def tearDown(self):
        self.fm_patcher.stop()

    def _get_msg(self):
        msg = Message()
        msg["From"] = "dummy@example.com"
        msg["Date"] = "Mon, 20 Nov 1995 19:12:08 -0500"
        msg["Message-ID"] = "<dummy>"
        msg["Message-ID-Hash"] = "QKODQBCADMDSP5YPOPKECXQWEQAMXZL3"
        msg.set_payload("Dummy message")
        return msg

    def test_irrelevant_api(self):
        self.assertIsNone(self.archiver.list_url(self.mlist))
        self.assertIsNone(self.archiver.permalink(self.mlist, self._get_msg()))

    def test_archive_message(self):
        msg = self._get_msg()
        with patch("mailman3_fedmsg_plugin._log") as logger:
            self.archiver.archive_message(self.mlist, msg)
        self.assertEqual(self.fm.publish.call_count, 1)
        sent_message = self.fm.publish.call_args[0][0]
        sent_message.validate()
        self.assertEqual(sent_message.topic, "mailman.receive.v1")
        self.assertEqual(sent_message.message_id, "<dummy>")
        self.assertEqual(sent_message.sender, "dummy@example.com")
        self.assertEqual(sent_message.date.isoformat(), "1995-11-20T19:12:08-05:00")
        self.assertTrue(logger.debug.called)
        self.assertEqual(
            logger.debug.call_args[0],
            ("Publishing %r to %r", "<dummy>", "mailman.receive.v1"),
        )

    def test_archive_message_error(self):
        msg = self._get_msg()
        self.fm.publish.side_effect = RuntimeError()
        with patch("mailman3_fedmsg_plugin._log") as logger:
            self.archiver.archive_message(self.mlist, msg)
        self.assertEqual(self.fm.publish.call_count, 1)
        self.assertTrue(logger.exception.called)
        self.assertEqual(
            logger.exception.call_args[0],
            (
                'Publishing "%r" on topic "%r" failed (%r)',
                "<dummy>", "mailman.receive.v1",
                self.fm.publish.side_effect,
            ),
        )

    def test_archive_message_excluded(self):
        msg = self._get_msg()
        mlist = FakeList("excluded@lists.example.com")
        self.archiver.archive_message(mlist, msg)
        self.assertFalse(self.fm.publish.called, 0)
