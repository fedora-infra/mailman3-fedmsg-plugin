import pytest
from unittest.mock import Mock, patch
from mailman3_fedmsg_plugin import Archiver

@pytest.fixture
def mock_mailing_list():
    return Mock()

@pytest.fixture
def mock_message():
    return Mock()

class MockMailingList:
    def __init__(self, list_name, mail_host, fqdn_listname, list_id, display_name):
        self.list_name = list_name
        self.mail_host = mail_host
        self.fqdn_listname = fqdn_listname
        self.list_id = list_id
        self.display_name = display_name

class MockMessage:
    def __init__(self, archived_at, delivered_to, from_, cc, to, in_reply_to, message_id, subject, x_message_id_hash, references, x_mailman_rule_hits, x_mailman_rule_misses, user_agent):
        self.archived_at = archived_at
        self.delivered_to = delivered_to
        self.from_ = from_
        self.cc = cc
        self.to = to
        self.in_reply_to = in_reply_to
        self.message_id = message_id
        self.subject = subject
        self.x_message_id_hash = x_message_id_hash
        self.references = references
        self.x_mailman_rule_hits = x_mailman_rule_hits
        self.x_mailman_rule_misses = x_mailman_rule_misses
        self.user_agent = user_agent

def test_archive_message():
    # Initialize the Archiver object
    archiver = Archiver()

    # Create mock objects with custom mock classes
    mock_mailing_list = MockMailingList(
        list_name="Test List",
        mail_host="example.com",
        fqdn_listname="test@example.com",
        list_id="12345",
        display_name="Test List"
    )
    mock_message = MockMessage(
        archived_at="2024-03-13T12:00:00",
        delivered_to="recipient@example.com",
        from_="sender@example.com",
        cc="cc@example.com",
        to="recipient@example.com",
        in_reply_to=None,
        message_id="123456789",
        subject="Test Subject",
        x_message_id_hash="abcdef123",
        references=[],
        x_mailman_rule_hits=0,
        x_mailman_rule_misses=0,
        user_agent="Test User Agent"
    )

    # Patch the safe_publish function to track its calls
    with patch('mailman3_fedmsg_plugin.safe_publish') as mock_safe_publish:
        # Call the archive_message method with mock objects
        archiver.archive_message(mock_mailing_list, mock_message)

        # Assert that safe_publish was called with the expected body
        expected_body = {
            "msg": {
                "archived-at": mock_message.archived_at,
                "delivered-to": mock_message.delivered_to,
                "from": mock_message.from_,
                "cc": mock_message.cc,
                "to": mock_message.to,
                "in-reply-to": mock_message.in_reply_to,
                "message-id": mock_message.message_id,
                "subject": mock_message.subject,
                "x-message-id-hash": mock_message.x_message_id_hash,
                "references": mock_message.references,
                "x-mailman-rule-hits": mock_message.x_mailman_rule_hits,
                "x-mailman-rule-misses": mock_message.x_mailman_rule_misses,
                "user-agent": mock_message.user_agent,
            },
            "mlist": {
                "list_name": mock_mailing_list.list_name,
                "mail_host": mock_mailing_list.mail_host,
                "fqdn_listname": mock_mailing_list.fqdn_listname,
                "list_id": mock_mailing_list.list_id,
                "display_name": mock_mailing_list.display_name,
            }
        }
        mock_safe_publish.assert_called_once_with(expected_body)
