# SPDX-FileCopyrightText: 2024 Contributors to the Fedora Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import logging
from unittest.mock import patch

import pytest
from fedora_messaging.config import conf as fm_conf
from fedora_messaging.exceptions import ConnectionException
from fedora_messaging.testing import mock_sends
from mailman.email.message import Message

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


@pytest.fixture()
def fm_config():
    test_config = {
        "excluded_lists": ["excluded.lists.example.com"],
        "archive_base_url": "http://hyperkitty.example.com/",
        "owned_domains": ["example.com"],
    }
    with patch.dict(fm_conf["consumer_config"], test_config):
        yield


@pytest.fixture
def archiver(fm_config):
    return Archiver()


@pytest.fixture
def mlist(fm_config):
    return FakeList("listname@lists.example.com")


@pytest.fixture
def msg():
    msg = Message()
    msg["From"] = "dummy@example.com"
    msg["To"] = "listname@lists.example.com"
    msg["Date"] = "Mon, 20 Nov 1995 19:12:08 -0500"
    msg["Message-ID"] = "<dummy>"
    msg["Message-ID-Hash"] = "QKODQBCADMDSP5YPOPKECXQWEQAMXZL3"
    msg.set_payload("Dummy message")
    return msg


def _publish(archiver, mlist, msg):
    # with mock_sends(MessageV1(topic="mailman.receive", body=expected_body)):
    with patch("mailman3_fedmsg_plugin.api.publish") as publish:
        archiver.archive_message(mlist, msg)

    publish.assert_called_once()
    return publish.call_args[0][0]


def test_irrelevant_api(archiver, mlist, msg):
    assert archiver.list_url(mlist) is None
    assert archiver.permalink(mlist, msg) is None


def test_archive_message(archiver, mlist, msg, caplog):
    caplog.set_level(logging.DEBUG)
    expected_body = {
        "mlist": {
            "display_name": "Listname",
            "fqdn_listname": "listname@lists.example.com",
            "list_id": "listname.lists.example.com",
            "list_name": "listname",
            "mail_host": "lists.example.com",
        },
        "msg": {
            "date": "Mon, 20 Nov 1995 19:12:08 -0500",
            "from": "dummy@example.com",
            "to": "listname@lists.example.com",
            "recipients": ["listname@lists.example.com"],
            "message-id": "<dummy>",
            "message-id-hash": "QKODQBCADMDSP5YPOPKECXQWEQAMXZL3",
        },
        "url": None,
        "usernames": ["dummy"],
        "sender_username": "dummy",
    }
    sent_message = _publish(archiver, mlist, msg)
    assert sent_message.topic == "mailman.receive"
    assert sent_message.body == expected_body

    logged_messages = [r for r in caplog.records if r.name == "mailman.archiver"]
    assert len(logged_messages) == 1
    logged_message = logged_messages[0]
    assert logged_message.levelname == "DEBUG"
    assert logged_message.message == "Publishing '<dummy>' to 'mailman.receive'"


@pytest.mark.parametrize(
    "archived_at,url",
    [
        ("http://example.com/dummy", "http://example.com/dummy"),
        ("<http://example.com/dummy>", "http://example.com/dummy"),
        ("dummy", "http://hyperkitty.example.com/dummy"),
    ],
)
def test_archive_message_url(archiver, mlist, msg, archived_at, url):
    msg["Archived-At"] = archived_at
    sent_message = _publish(archiver, mlist, msg)
    assert sent_message.url == url


def test_archive_message_no_url(archiver, mlist, msg):
    msg["Archived-At"] = "dummy"
    with patch.dict(fm_conf["consumer_config"], {"archive_base_url": None}):
        sent_message = _publish(archiver, mlist, msg)
    assert sent_message.url is None


def test_archive_message_handle_bogus_address(archiver, mlist, msg):
    msg["Cc"] = "@bogus@"
    sent_message = _publish(archiver, mlist, msg)
    assert sent_message.body["msg"]["recipients"] == [mlist.fqdn_listname]


def test_archive_message_from_elsewhere(archiver, mlist, msg):
    msg.replace_header("From", "dummy@somewhere-else.com")
    sent_message = _publish(archiver, mlist, msg)
    assert sent_message.body["sender_username"] is None


def test_archive_message_error(archiver, mlist, msg, caplog):
    error = ConnectionException()
    with patch("mailman3_fedmsg_plugin.api") as fm_api:
        fm_api.publish.side_effect = error
        archiver.archive_message(mlist, msg)

    assert fm_api.publish.call_count == 3
    logged_messages = [r for r in caplog.records if r.name == "mailman.archiver"]
    assert len(logged_messages) == 3
    for logged_message in logged_messages[:2]:
        assert logged_message.levelname == "WARNING"
        assert (
            logged_message.message
            == "Publishing '<dummy>' to 'mailman.receive' failed. Retrying. ConnectionException"
        )
    logged_message = logged_messages[2]
    assert logged_message.levelname == "ERROR"
    assert (
        logged_message.message
        == "Publishing '<dummy>' to 'mailman.receive' failed. Giving up. ConnectionException"
    )


def test_archive_message_excluded(archiver, msg):
    mlist = FakeList("excluded@lists.example.com")
    with mock_sends():
        archiver.archive_message(mlist, msg)
