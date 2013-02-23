OpenDKIM-Fedora
===============

This git repo contains:

- SPECS/opendkim.spec - spec file for the OpenDKIM package I maintain in Fedora & EPEL (https://admin.fedoraproject.org/pkgdb/acls/name/opendkim/)

- PATCHES - patches for the spec file, as needed, depending on version

- contrib/init/redhat/opendkim.in - Template file to build the OpenDKIM SysV init script (contributed to OpenDKIM source)

- contrib/init/redhat/opendkim.service.in - Template file to build the OpenDKIM systemd service file (contributed to OpenDKIM source)

- contrib/init/redhat/opendkim-default-keygen.in - Template file to build the external script that generates default DKIM keys on startup (contributed to OpenDKIM source)

CONTRIBUTORS: Please do pull requests in the "develop" branch only. The "master" branch is just for release versions. Thanks!

For official source code and documentation, please visit http://opendkim.org/

Steve Jenkins
http://stevejenkins.com/ - http://stevej.fedorapeople.org/


