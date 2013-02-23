OpenDKIM-Fedora
===============

This git repo contains:

- SPECS/opendkim.spec - systemd version of the spec file for the OpenDKIM package I maintain in Fedora & EPEL

- PATCHES - patches for the spec file, as needed, depending on version

- contrib/init/redhat/opendkim.service.in - Template file for the OpenDKIM systemd service file (included in OpenDKIM source)

- contrib/init/redhat/opendkim-default-keygen.in - Template file for a script that generates default DKIM keys on startup (included in OpenDKIM source)

CONTRIBUTORS: Please do pull requests in the "develop" branch only. The "master" branch is just for release versions. Thanks!

For official source code and documentation, please visit:

http://opendkim.org/
