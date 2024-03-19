# Copyright (C) 2018  Red Hat, Inc.
# SPDX-FileCopyrightText: 2024 Contributors to the Fedora Project
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import pytest
from mailman3_fedmsg_plugin_schemas import MessageV1


@pytest.fixture
def body():
    return {
        "mlist": {
            "display_name": "List",
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
            "subject": "dummy subject",
            "message-id": "<dummy>",
            "message-id-hash": "QKODQBCADMDSP5YPOPKECXQWEQAMXZL3",
        },
        "usernames": ["dummy"],
        "sender_username": "dummy",
    }


def test_schema(body):
    message = MessageV1(topic="mailman.receive", body=body)
    assert message.topic == "mailman.receive"
    assert message.message_id == "<dummy>"
    assert message.sender == "dummy@example.com"
    assert message.date.isoformat() == "1995-11-20T19:12:08-05:00"
    assert message.list_id == "listname.lists.example.com"
    assert message.usernames == ["dummy"]
    assert message.recipients == ["listname@lists.example.com"]
    assert message.summary == "dummy wrote 'dummy subject' to the listname list"
    assert message.url is None
    assert message.app_icon == "https://apps.fedoraproject.org/img/icons/hyperkitty.png"
    assert message.agent_avatar == (
        "https://seccdn.libravatar.org/avatar/"
        "963dd12f8d2f181ee9bef66a67f7b3bd87f47e9e3ecc5b534c85766b227daa28"
        "?s=64&d=retro"
    )
    assert str(message) == (
        "From: dummy@example.com\n"
        "Date: 1995-11-20 19:12:08-05:00\n"
        "List-Id: listname.lists.example.com\n"
        "Subject: dummy subject\n"
    )


def test_schema_reply(body):
    body["msg"]["in-reply-to"] = "<dummy2>"
    message = MessageV1(topic="mailman.receive", body=body)
    assert message.summary == "On the listname list, dummy replied to 'dummy subject'"


def test_schema_summary_from_elsewhere(body):
    body["sender_username"] = None
    message = MessageV1(topic="mailman.receive", body=body)
    assert message.summary == "someone wrote 'dummy subject' to the listname list"


def test_schema_list_in_rcpt(body):
    body["msg"]["to"] = "@bogus@"
    body["msg"]["cc"] = body["mlist"]["fqdn_listname"]
    message = MessageV1(topic="mailman.receive", body=body)
    # Neither the list address nor the bogus value must be in there
    assert message.usernames == ["dummy"]
