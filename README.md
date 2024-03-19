# Mailman3 Fedmsg plugin

Publish notifications about emails to the Fedora Messaging bus.

Enable this by adding the following to your `mailman.cfg` file:

```
[archiver.fedora_messaging]
# The class implementing the IArchiver interface.
class: mailman3_fedmsg_plugin.Archiver
enable: yes
```

Your Fedora Messaging configuration file must be working.

You can exclude certain lists from publication by adding them to the
`excluded_lists` key in the Fedora Messaging configuration files's
`[consumer_config]` section:

```
[consumer_config]
excluded_lists = ["bugzilla.lists.fedoraproject.org, commits.lists.fedoraproject.org"]
```

The values must be the list ID (dotted format) and they must be separated by
commas if you want to exclude multiple lists.

In this section, you can also set the URL of the HyperKitty instance
where the messages are archived, if any:

```
[consumer_config]
archive_base_url = "https://lists.fedoraproject.org/archives/"
```

In the same section, you can set the list of domains that the plugin can
extract usernames from:

```
[consumer_config]
# Domains where we can extract the username from the address
owned_domains = ["fedoraproject.org", "centos.org"]
```
