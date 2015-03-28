%global systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7)

Summary: A DomainKeys Identified Mail (DKIM) milter to sign and/or verify mail
Name: opendkim
Version: 2.10.1
Release: 7%{?dist}
Group: System Environment/Daemons
License: BSD and Sendmail
URL: http://opendkim.org/
Source0: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz

# Required for all versions
Requires: lib%{name}%{?_isa} = %{version}-%{release}
Requires: sendmail-milter, libbsd
BuildRequires: sendmail-devel, openssl-devel, libtool, pkgconfig, libbsd-devel
Requires (pre): shadow-utils
Requires (post): policycoreutils, policycoreutils-python

%if %systemd
# Required for systemd
Requires (post): systemd-units
Requires (preun): systemd-units
Requires (postun): systemd-units
Requires (post): systemd-sysv
BuildRequires: libdb-devel
BuildRequires: libmemcached-devel
%else
# Required for SysV
Requires (post): chkconfig
Requires (preun): chkconfig, initscripts
Requires (postun): initscripts
BuildRequires: db4-devel
%endif

Patch0: %{name}.init.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
OpenDKIM allows signing and/or verification of email through an open source
library that implements the DKIM service, plus a milter-based filter
application that can plug in to any milter-aware MTA, including sendmail,
Postfix, or any other MTA that supports the milter protocol.

%package -n libopendkim
Summary: An open source DKIM library
Group: System Environment/Libraries

%description -n libopendkim
This package contains the library files required for running services built
using libopendkim.

%package -n libopendkim-devel
Summary: Development files for libopendkim
Group: Development/Libraries
Requires: lib%{name}%{?_isa} = %{version}-%{release}

%description -n libopendkim-devel
This package contains the static libraries, headers, and other support files
required for developing applications against libopendkim.

%prep
%setup -q
%if %systemd
# Apply systemd patches
#%patch0 -p1
%else
# Apply SysV patches
%patch0 -p1
%endif

%build
# Always use system libtool instead of opendkim provided one to
# properly handle 32 versus 64 bit detection and settings
%define LIBTOOL LIBTOOL=`which libtool`

%if %systemd
%configure --with-libmemcached --with-db
%else
%configure --with-db
%endif

# Remove rpath
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

%install
rm -rf %{buildroot}

make DESTDIR=%{buildroot} install %{?_smp_mflags}
install -d %{buildroot}%{_sysconfdir}
install -d %{buildroot}%{_sysconfdir}/sysconfig
install -m 0755 contrib/init/redhat/%{name}-default-keygen %{buildroot}%{_sbindir}/%{name}-default-keygen

%if %systemd
install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 contrib/systemd/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
%else
install -d %{buildroot}%{_initrddir}
install -m 0755 contrib/init/redhat/%{name} %{buildroot}%{_initrddir}/%{name}
%endif

cat > %{buildroot}%{_sysconfdir}/%{name}.conf << 'EOF'
## BASIC OPENDKIM CONFIGURATION FILE
## See %{name}.conf(5) or %{_defaultdocdir}/%{name}/%{name}.conf.sample for more

## BEFORE running OpenDKIM you must:

## - make your MTA (Postfix, Sendmail, etc.) aware of OpenDKIM
## - generate keys for your domain (if signing)
## - edit your DNS records to publish your public keys (if signing)

## See %{_defaultdocdir}/%{name}/INSTALL for detailed instructions.

## CONFIGURATION OPTIONS

# Specifies the path to the process ID file.
PidFile	%{_localstatedir}/run/%{name}/%{name}.pid

# Selects operating modes. Valid modes are s (sign) and v (verify). Default is v.
# Must be changed to s (sign only) or sv (sign and verify) in order to sign outgoing
# messages.
Mode	v

# Log activity to the system log.
Syslog	yes

# Log additional entries indicating successful signing or verification of messages.
SyslogSuccess	yes

# If logging is enabled, include detailed logging about why or why not a message was
# signed or verified. This causes an increase in the amount of log data generated
# for each message, so set this to No (or comment it out) if it gets too noisy.
LogWhy	yes

# Attempt to become the specified user before starting operations.
UserID	%{name}:%{name}

# Create a socket through which your MTA can communicate.
Socket	inet:8891@localhost

# Required to use local socket with MTAs that access the socket as a non-
# privileged user (e.g. Postfix)
Umask	002

# This specifies a text file in which to store DKIM transaction statistics.
# OpenDKIM must be manually compiled with --enable-stats to enable this feature.
#Statistics	%{_localstatedir}/spool/%{name}/stats.dat

## SIGNING OPTIONS

# Selects the canonicalization method(s) to be used when signing messages.
Canonicalization	relaxed/relaxed

# Domain(s) whose mail should be signed by this filter. Mail from other domains will
# be verified rather than being signed. Uncomment and use your domain name.
# This parameter is not required if a SigningTable is in use.
#Domain	example.com

# Defines the name of the selector to be used when signing messages.
Selector	default

# Specifies the minimum number of key bits for acceptable keys and signatures.
MinimumKeyBits 1024

# Gives the location of a private key to be used for signing ALL messages. This
# directive is ignored if KeyTable is enabled.
KeyFile	%{_sysconfdir}/%{name}/keys/default.private

# Gives the location of a file mapping key names to signing keys. In simple terms,
# this tells OpenDKIM where to find your keys. If present, overrides any KeyFile
# directive in the configuration file. Requires SigningTable be enabled.
#KeyTable	%{_sysconfdir}/%{name}/KeyTable

# Defines a table used to select one or more signatures to apply to a message based
# on the address found in the From: header field. In simple terms, this tells
# OpenDKIM how to use your keys. Requires KeyTable be enabled.
#SigningTable	refile:%{_sysconfdir}/%{name}/SigningTable

# Identifies a set of "external" hosts that may send mail through the server as one
# of the signing domains without credentials as such.
#ExternalIgnoreList	refile:%{_sysconfdir}/%{name}/TrustedHosts

# Identifies a set "internal" hosts whose mail should be signed rather than verified.
#InternalHosts	refile:%{_sysconfdir}/%{name}/TrustedHosts
EOF

cat > %{buildroot}%{_sysconfdir}/sysconfig/%{name} << 'EOF'
# Set the necessary startup options
OPTIONS="-x %{_sysconfdir}/%{name}.conf -P %{_localstatedir}/run/%{name}/%{name}.pid"

# Set the default DKIM selector
DKIM_SELECTOR=default

# Set the default DKIM key location
DKIM_KEYDIR=%{_sysconfdir}/%{name}/keys
EOF

mkdir -p %{buildroot}%{_sysconfdir}/%{name}
cat > %{buildroot}%{_sysconfdir}/%{name}/SigningTable << 'EOF'
# OPENDKIM SIGNING TABLE
# This table controls how to apply one or more signatures to outgoing messages based
# on the address found in the From: header field. In simple terms, this tells
# OpenDKIM "how" to apply your keys.

# To use this file, uncomment the SigningTable option in %{_sysconfdir}/%{name}.conf,
# then uncomment one of the usage examples below and replace example.com with your
# domain name, then restart OpenDKIM.

# WILDCARD EXAMPLE
# Enables signing for any address on the listed domain(s), but will work only if
# "refile:%{_sysconfdir}/%{name}/SigningTable" is included in %{_sysconfdir}/%{name}.conf.
# Create additional lines for additional domains.

#*@example.com default._domainkey.example.com

# NON-WILDCARD EXAMPLE
# If "file:" (instead of "refile:") is specified in %{_sysconfdir}/%{name}.conf, then
# wildcards will not work. Instead, full user@host is checked first, then simply host,
# then user@.domain (with all superdomains checked in sequence, so "foo.example.com"
# would first check "user@foo.example.com", then "user@.example.com", then "user@.com"),
# then .domain, then user@*, and finally *. See the %{name}.conf(5) man page under
# "SigningTable" for more details.

#example.com default._domainkey.example.com
EOF

cat > %{buildroot}%{_sysconfdir}/%{name}/KeyTable << 'EOF'
# OPENDKIM KEY TABLE
# To use this file, uncomment the #KeyTable option in %{_sysconfdir}/%{name}.conf,
# then uncomment the following line and replace example.com with your domain
# name, then restart OpenDKIM. Additional keys may be added on separate lines.

#default._domainkey.example.com example.com:default:%{_sysconfdir}/%{name}/keys/default.private
EOF

cat > %{buildroot}%{_sysconfdir}/%{name}/TrustedHosts << 'EOF'
# OPENDKIM TRUSTED HOSTS
# To use this file, uncomment the #ExternalIgnoreList and/or the #InternalHosts
# option in %{_sysconfdir}/%{name}.conf then restart OpenDKIM. Additional hosts
# may be added on separate lines (IP addresses, hostnames, or CIDR ranges).
# The localhost IP (127.0.0.1) should always be the first entry in this file.
127.0.0.1
::1
#host.example.com
#192.168.1.0/24
EOF

cat > README.fedora << 'EOF'
#####################################
#FEDORA-SPECIFIC README FOR OPENDKIM#
#####################################
Last updated: Mar 3, 2015 by Steve Jenkins (steve@stevejenkins.com)

Generating keys for OpenDKIM
============================
After installing the opendkim package, you MUST generate a pair of keys (public and private) before
attempting to start the opendkim service.

A valid private key must exist in the location expected by /etc/opendkim.conf before the service will start.

A matching public key must be included in your domain's DNS records before remote systems can validate
your outgoing mail's DKIM signature.


Generating Keys Automatically
=============================
To automatically create a pair of default keys for the local domain, do:

% sudo /usr/sbin/opendkim-default-keygen

The default keygen script will attempt to fetch the local domain name, generate a private and public key for
the domain, then save them in /etc/opendkim/keys as default.private and default.txt with the proper
ownership and permissions.

NOTE: The default key generation script MUST be run by a privileged user (or root). Otherwise, the resulting
private key ownership and permissions will not be correct.


Generating Keys Manually
========================
A privileged user (or root) can manually generate a set of keys by doing the following:

1) Create a directory to store the new keys:

% sudo mkdir /etc/opendkim/keys/example.com

2) Generate keys in that directory for a specific domain name and selector:

% sudo /usr/sbin/opendkim-genkey -D /etc/opendkim/keys/example.com/ -d example.com -s default

3) Set the proper ownership for the directory and private key:

% sudo chown -R root:opendkim /etc/opendkim/keys/example.com

4) Set secure permissions for the private key:

% sudo chmod 640 /etc/opendkim/keys/example.com/default.private

5) Set standard permissions for the public key:

% sudo chmod 644 /etc/opendkim/keys/example.com/default.txt


Updating Key Location(s) in Configuration Files
===============================================
If you run the opendkim-default-keygen script, the default keys will be saved in /etc/opendkim/keys as
default.private and default.txt, which is the location expected by the default /etc/opendkim.conf file.

If you manually generate your own keys, you must update the key location and name in /etc/opendkim.conf
before attempting to start the opendkim service.


Additional Configuration Help
=============================
For help configuring your MTA (Postfix, Sendmail, etc.) with OpenDKIM, setting up DNS records with your
public DKIM key, as well as instructions on configuring OpenDKIM to sign outgoing mail for multiple
domains, follow the how-to at:

http://wp.me/p1iGgP-ou

Official documentation for OpenDKIM is available at http://opendkim.org/

OpenDKIM mailing lists are available at http://lists.opendkim.org/

###
EOF

install -p -d %{buildroot}%{_sysconfdir}/tmpfiles.d
cat > %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf <<'EOF'
D %{_localstatedir}/run/%{name} 0700 %{name} %{name} -
EOF

rm -r %{buildroot}%{_prefix}/share/doc/%{name}
rm %{buildroot}%{_libdir}/*.a
rm %{buildroot}%{_libdir}/*.la

mkdir -p %{buildroot}%{_localstatedir}/spool/%{name}
mkdir -p %{buildroot}%{_localstatedir}/run/%{name}
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir %{buildroot}%{_sysconfdir}/%{name}/keys

install -m 0755 stats/%{name}-reportstats %{buildroot}%{_prefix}/sbin/%{name}-reportstats
sed -i 's|^OPENDKIMSTATSDIR="/var/db/opendkim"|OPENDKIMSTATSDIR="%{_localstatedir}/spool/%{name}"|g' %{buildroot}%{_prefix}/sbin/%{name}-reportstats
sed -i 's|^OPENDKIMDATOWNER="mailnull:mailnull"|OPENDKIMDATOWNER="%{name}:%{name}"|g' %{buildroot}%{_prefix}/sbin/%{name}-reportstats

chmod 0644 contrib/convert/convert_keylist.sh

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
	useradd -r -g %{name} -G mail -d %{_localstatedir}/run/%{name} -s /sbin/nologin \
	-c "OpenDKIM Milter" %{name}
exit 0

%post
%if %systemd
if [ $1 -eq 1 ] ; then 
    # Initial installation 
    /bin/systemctl enable %{name}.service >/dev/null 2>&1 || :
fi

%else

/sbin/chkconfig --add %{name} || :
%endif

%preun
%if %systemd
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable %{name}.service > /dev/null 2>&1 || :
    /bin/systemctl stop %{name}.service > /dev/null 2>&1 || :
fi

%else

if [ $1 -eq 0 ]; then
	service %{name} stop >/dev/null || :
	/sbin/chkconfig --del %{name} || :
fi
exit 0
%endif

%postun
%if %systemd
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
fi

%else

if [ "$1" -ge "1" ] ; then
	/sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
exit 0
%endif

%if %systemd
%triggerun -- %{name} < 2.8.0-1
/bin/systemctl enable %{name}.service >/dev/null 2>&1
/sbin/chkconfig --del %{name} >/dev/null 2>&1 || :
/bin/systemctl try-restart %{name}.service >/dev/null 2>&1 || :
%endif

%post -n libopendkim -p /sbin/ldconfig

%postun -n libopendkim -p /sbin/ldconfig

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc FEATURES KNOWNBUGS LICENSE LICENSE.Sendmail RELEASE_NOTES RELEASE_NOTES.Sendmail INSTALL
%doc contrib/convert/convert_keylist.sh %{name}/*.sample
%doc %{name}/%{name}.conf.simple-verify %{name}/%{name}.conf.simple
%doc %{name}/README contrib/lua/*.lua
%doc README.fedora
%config(noreplace) %{_sysconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/tmpfiles.d/%{name}.conf
%config(noreplace) %attr(0640,%{name},%{name}) %{_sysconfdir}/%{name}/SigningTable
%config(noreplace) %attr(0640,%{name},%{name}) %{_sysconfdir}/%{name}/KeyTable
%config(noreplace) %attr(0640,%{name},%{name}) %{_sysconfdir}/%{name}/TrustedHosts
%config(noreplace) %{_sysconfdir}/sysconfig/%{name}
%{_sbindir}/*
%{_mandir}/*/*
%dir %attr(-,%{name},%{name}) %{_localstatedir}/spool/%{name}
%dir %attr(0775,%{name},%{name}) %{_localstatedir}/run/%{name}
%dir %attr(-,root,%{name}) %{_sysconfdir}/%{name}
%dir %attr(0750,%name,%{name}) %{_sysconfdir}/%{name}/keys
%attr(0755,root,root) %{_sbindir}/%{name}-default-keygen

%if %systemd
%attr(0644,root,root) %{_unitdir}/%{name}.service
%else
%attr(0755,root,root) %{_initrddir}/%{name}
%endif

%files -n libopendkim
%defattr(-,root,root)
%doc LICENSE LICENSE.Sendmail README
%{_libdir}/libopendkim.so.*

%files -n libopendkim-devel
%defattr(-,root,root)
%doc LICENSE LICENSE.Sendmail
%doc libopendkim/docs/*.html
%{_includedir}/%{name}
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc

%changelog
* Sat Mar 28 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-7
- added %{?_isa} to Requires where necessary
- added sendmail-milter to Requires
- added libtool to BuildRequires
- moved libbsd from BuildRequires to Requires
- added policycoreutils and policycoreutils-python to Requires (post)

* Sat Mar 28 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-6
- Remove global _pkgdocdir variable
- Use defaultdocdir variable in default config file
- Setting permissions special mode bit explicitly in all cases for consistency
- Change /var/run/opendkim permissions to group writable for Bug #1120080

* Wed Mar 25 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-5
- Combined systemd and SysV spec files using conditionals
- Drop sysvinit subpackage completely

* Tue Mar 24 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-4
- Fixed typo in Group name
- Added updated libtool definition
- Additional comments in spec file
- Patch SysV initscript to stop default key generation on startup

* Thu Mar 05 2015 Adam Jackson <ajax@redhat.com> 2.10.1-3
- Drop sysvinit subpackage from F23+

* Tue Mar 03 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-2
- Added IPv6 ::1 support to TrustedHosts (RH Bugzilla #1049204)

* Tue Mar 03 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-1
- Updated to use newer upstream 2.10.1 source code

* Tue Dec 09 2014 Steve Jenkins <steve@stevejenkins.com> - 2.10.0-1
- Updated to use newer upstream 2.10.0 source code
- Removed unbound compile option due to orphaned upstream dependency
- Removed AUTOCREATE_DKIM_KEYS option
- Added README.fedora with basic key generation and config instructions

* Sun Aug 17 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Mon Aug 04 2014 Steve Jenkins <steve@stevejenkins.com> - 2.9.2-2
- Change file ownerships/permissions to fix https://bugzilla.redhat.com/show_bug.cgi?id=891292
- Default keys no longer created on startup. Privileged user must run opendkim-default-keygen or create manually (after install)

* Wed Jul 30 2014 Steve Jenkins <steve@stevejenkins.com> - 2.9.2-1
- Updated to use newer upstream 2.9.2 source code
- Fixed invalid date in changelog

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.9.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Dec 18 2013 Steve Jenkins <steve stevejenkins com> - 2.9.0-2
- Patch adds user and group to systemd service file (Thx jcosta@redhat.com)
- Changed default ownership of /etc/opendkim/keys directory to opendkim user

* Wed Dec 18 2013 Steve Jenkins <steve stevejenkins com> - 2.9.0-1
- Updated to use newer upstream 2.9.0 source code
- Added libbsd-devel to Build Requires
- Removed listrl references from libopendkim files section (handled by libbsd-devel)

* Sun Nov 3 2013 Steve Jenkins <steve stevejenkins com> - 2.8.4-4
- Rebuild of all release packages to sync version numbers

* Sun Nov 3 2013 Ville Skytta ville.skytta@iki.fi> - 2.8.4-3
- Fix path to docs in sample config when doc dir is unversioned (#993997).

* Sat Aug 03 2013 Petr Pisar <ppisar@redhat.com> - 2.8.4-2
- Perl 5.18 rebuild

* Tue Jul 23 2013 Steve Jenkins <steve stevejenkins com> 2.8.4-1
- Updated to use newer upstream 2.8.4 source code
- Added libbsd build requirement

* Thu Jul 18 2013 Petr Pisar <ppisar@redhat.com> - 2.8.3-3
- Perl 5.18 rebuild

* Fri May 17 2013 Steve Jenkins <steve stevejenkins com> 2.8.3-2
- Removed libmemcached support from SysV version (requires > v0.36)

* Sun May 12 2013 Steve Jenkins <steve stevejenkins com> 2.8.3-1
- Updated to use newer upstream 2.8.3 source code
- Added unbound, libmcached, and db support on configure

* Mon Apr 29 2013 Steve Jenkins <steve stevejenkins com> 2.8.2-1
- Updated to use newer upstream 2.8.2 source code

* Tue Mar 19 2013 Steve Jenkins <steve stevejenkins com> 2.8.1-1
- Updated to use newer upstream 2.8.1 source code
- Removed patches for bugs fixed in upstream source

* Wed Feb 27 2013 Steve Jenkins <steve stevejenkins com> 2.8.0-4
- Added patch from upstream to fix libdb compatibility issues

* Tue Feb 26 2013 Steve Jenkins <steve stevejenkins com> 2.8.0-3
- Split into two spec files: systemd (F17+) and SysV (EL5-6)
- Removed leading / from unitdir variables
- Removed commented source lines
- Created comment sections for easy switching between systemd and SysV

* Mon Feb 25 2013 Steve Jenkins <steve stevejenkins com> 2.8.0-2
- Added / in front of unitdir variables

* Thu Feb 21 2013 Steve Jenkins <steve stevejenkins com> 2.8.0-1
- Happy Birthday to me! :)
- Updated to use newer upstream 2.8.0 source code
- Migration from SysV initscript to systemd unit file
- Added systemd build requirement
- Edited comments in default configuration files
- Changed default Canonicalization to relaxed/relaxed in config file
- Changed default values in EnvironmentFile
- Moved program startup options into EnvironmentFile
- Moved default key check and generation on startup to external script
- Removed AutoRestart directives from default config (systemd will handle)
- Incorporated additional variable names throughout spec file
- Added support for new opendkim-sysvinit package for legacy SysV systems

* Tue Jan 08 2013 Steve Jenkins <steve stevejenkins com> 2.7.4-1
- Updated to use newer upstream 2.7.4 source code
- Added AutoRestart and AutoRestartRate directives to default configuration
- Changed default SigningTable directive to include refile: for wildcard support

* Tue Dec 04 2012 Steve Jenkins <steve stevejenkins com> 2.7.3-2
- Set /etc/opendkim/keys default permissions to 750 (Thanks patrick at puzzled.xs4al.nl)

* Thu Nov 29 2012 Steve Jenkins <steve stevejenkins com> 2.7.3-1
- Updated to use newer upstream 2.7.3 source code

* Mon Nov 19 2012 Steve Jenkins <steve stevejenkins com> 2.7.2-1
- Updated to use newer upstream 2.7.2 source code

* Tue Oct 30 2012 Steve Jenkins <steve stevejenkins com> 2.7.1-1
- Updated to use newer upstream 2.7.1 source code
- Updated to reflect source code move of files from /usr/bin to /usr/sbin
- Removed --enable-stats configure option to avoid additional dependencies
- Added support for strlcat() and strlcopy() previously in libopendkim
- Added new MinimumKeyBits configuration option with default of 1024

* Wed Aug 22 2012 Steve Jenkins <steve stevejenkins com> 2.6.7-1
- Updated to use newer upstream 2.6.7 source code
- Removed patches from 2.4.2 which were incorporated upstream
- Updated install directory of opendkim-reportstats

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.2-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.4.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Thu Sep 22 2011 Steve Jenkins <steve stevejenkins com> 2.4.2-5
- Changed ownernship of directories to comply with selinux-policy
- Added default KeyTable and TrustedHosts files
- Added config(noreplace) to sysconfig file

* Mon Sep 19 2011 Steve Jenkins <steve stevejenkins com> 2.4.2-4
- Use Fedora standard method to fix pkg supplied libtool (Todd Lyons)
- Updated Summary and Description
- Fixed default stats file location in sample config file
- Install opendkim-reportstats and README.opendkim-reportstats
- Changed default stop priority in init script
- Added example SigningTable
- Added sysconfig support for AUTOCREATE_DKIM_KEYS, DKIM_SELECTOR, DKIM_KEYDIR
- Enabled SysLogSuccess and LogWhy by default

* Mon Aug 22 2011 Steve Jenkins <steve stevejenkins com> 2.4.2-3
- Mad props to Matt Domsch for sponsoring and providing feedback
- Removed {?OSshort} variable in Release: header
- Removed explicit Requires: in header
- Added support for tmpfiles.d
- Replaced opendkim with {name} variable throughout
- Replaced RPM_BUILD_ROOT with {buildroot}
- Moved changelog to bottom of file
- Removed "All Rights Reserved" from top of spec file
- Removed Prefix: line in header
- Pointed Source*: to the upstream tarballs
- Changed BuildRoot: format
- Changed makeinstall to make install
- Moved creation of working dirs to install
- Moved ownership of working dirs to files
- Moved user and group creation to pre
- Moved permissions setting to files with attr
- Created directory for user keys
- Removed testing for working directories; mkdir -p will suffice
- Revised Summary
- Removed static libraries from -devel package
- Removed extra spaces
- Removed usermod command to add opendkim to mail group
- Removed echo in post
- General tidying up
- Moved INSTALL readme information into patch
- Removed CPPFLAGS from configure
- Added _smp_mflags to make
- Changed which README from source is written to doc directory
- Added licenses to all subpackages
- Changed default runlevel in init script

* Tue Aug 16 2011  Steve Jenkins <steve stevejenkins com> 2.4.2-2
- Added -q to setup -a 1
- Added x86_64 libtool support (Mad props to Todd Lyons)
- Added {?dist} variable support in Release: header
- Changed Statistics storage location
- Statistics option now commented in opendkim.conf by default
- Check for existing private key before attempting to build keys
- Check for domain name before attempting to build keys

* Mon Aug 15 2011  Steve Jenkins <steve stevejenkins com> 2.4.2-1
- Initial Packaging of opendkim
