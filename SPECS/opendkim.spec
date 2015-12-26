%global systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7)
%global upname OpenDKIM
%global bigname OPENDKIM

Summary: A DomainKeys Identified Mail (DKIM) milter to sign and/or verify mail
Name: opendkim
Version: 2.10.3
Release: 3%{?dist}
Group: System Environment/Daemons
License: BSD and Sendmail
URL: http://%{name}.org/
Source0: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz

# Required for all versions
Requires: lib%{name}%{?_isa} = %{version}-%{release}
BuildRequires: sendmail-devel, openssl-devel, libtool, pkgconfig, libbsd, libbsd-devel, opendbx-devel
Requires(pre): shadow-utils

%if 0%{?rhel} && 0%{?rhel} == 5
Requires(post): policycoreutils
%endif

%if %systemd
# Required for systemd
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units
Requires(post): systemd-sysv
BuildRequires: libdb-devel, libmemcached-devel
%else
# Required for SysV
Requires(post): chkconfig
Requires(preun): chkconfig, initscripts
Requires(postun): initscripts
BuildRequires: db4-devel
%endif

#Patch0: %{name}.init.patch

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
%{upname} allows signing and/or verification of email through an open source
library that implements the DKIM service, plus a milter-based filter
application that can plug in to any milter-aware MTA, including sendmail,
Postfix, or any other MTA that supports the milter protocol.

%package -n lib%{name}
Summary: An open source DKIM library
Group: System Environment/Libraries
Obsoletes: %{name}-sysvinit < 2.10.1-5

%description -n lib%{name}
This package contains the library files required for running services built
using libopendkim.

%package -n lib%{name}-devel
Summary: Development files for lib%{name}
Group: Development/Libraries
Requires: lib%{name}%{?_isa} = %{version}-%{release}

%description -n lib%{name}-devel
This package contains the static libraries, headers, and other support files
required for developing applications against libopendkim.

%prep
%setup -q
%if %systemd
# Apply systemd patches
#%patch0 -p1
%else
# Apply SysV patches
#%patch0 -p1
%endif

%build
# Always use system libtool instead of pacakge-provided one to
# properly handle 32 versus 64 bit detection and settings
%define LIBTOOL LIBTOOL=`which libtool`

%if %systemd
# Configure with options available to systemd
%configure --with-odbx --with-db --with-libmemcached --with-openldap
%else
# Configure with options available to SysV
%configure --with-odbx --with-db --with-openldap
%endif

# Remove rpath
%{__sed} -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
%{__sed} -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

%install
%{__make} DESTDIR=%{buildroot} install %{?_smp_mflags}
%{__install} -d %{buildroot}%{_sysconfdir}
%{__install} -d %{buildroot}%{_sysconfdir}/sysconfig
%{__install} -m 0755 contrib/init/redhat/%{name}-default-keygen %{buildroot}%{_sbindir}/%{name}-default-keygen

%if %systemd
%{__install} -d -m 0755 %{buildroot}%{_unitdir}
%{__install} -m 0644 contrib/systemd/%{name}.service %{buildroot}%{_unitdir}/%{name}.service
%else
%{__install} -d %{buildroot}%{_initrddir}
%{__install} -m 0755 contrib/init/redhat/%{name} %{buildroot}%{_initrddir}/%{name}
%endif

%{__cat} > %{buildroot}%{_sysconfdir}/%{name}.conf << 'EOF'
## BASIC %{bigname} CONFIGURATION FILE
## See %{name}.conf(5) or %{_defaultdocdir}/%{name}/%{name}.conf.sample for more

## BEFORE running %{upname} you must:

## - make your MTA (Postfix, Sendmail, etc.) aware of %{upname}
## - generate keys for your domain (if signing)
## - edit your DNS records to publish your public keys (if signing)

## See %{_defaultdocdir}/%{name}/INSTALL for detailed instructions.

## DEPRECATED CONFIGURATION OPTIONS
## 
## The following configuration options are no longer valid.  They should be
## removed from your existing configuration file to prevent potential issues.
## Failure to do so may result in %{name} being unable to start.
## 
## Removed in 2.10.0:
##   AddAllSignatureResults
##   ADSPAction
##   ADSPNoSuchDomain
##   BogusPolicy
##   DisableADSP
##   LDAPSoftStart
##   LocalADSP
##   NoDiscardableMailTo
##   On-PolicyError
##   SendADSPReports
##   UnprotectedPolicy

## CONFIGURATION OPTIONS

##  Specifies the path to the process ID file.
PidFile	%{_localstatedir}/run/%{name}/%{name}.pid

##  Selects operating modes. Valid modes are s (sign) and v (verify). Default is v.
##  Must be changed to s (sign only) or sv (sign and verify) in order to sign outgoing
##  messages.
Mode	v

##  Log activity to the system log.
Syslog	yes

##  Log additional entries indicating successful signing or verification of messages.
SyslogSuccess	yes

##  If logging is enabled, include detailed logging about why or why not a message was
##  signed or verified. This causes an increase in the amount of log data generated
##  for each message, so set this to No (or comment it out) if it gets too noisy.
LogWhy	yes

##  Attempt to become the specified user before starting operations.
UserID	%{name}:%{name}

##  Create a socket through which your MTA can communicate.
Socket	inet:8891@localhost

##  Required to use local socket with MTAs that access the socket as a non-
##  privileged user (e.g. Postfix)
Umask	002

##  This specifies a text file in which to store DKIM transaction statistics.
##  %{upname} must be manually compiled with --enable-stats to enable this feature.
# Statistics	%{_localstatedir}/spool/%{name}/stats.dat

##  Specifies whether or not the filter should generate report mail back
##  to senders when verification fails and an address for such a purpose
##  is provided. See opendkim.conf(5) for details.
SendReports	yes

##  Specifies the sending address to be used on From: headers of outgoing
##  failure reports.  By default, the e-mail address of the user executing
##  the filter is used (executing_user@hostname).
# ReportAddress	"Example.com Postmaster" <postmaster@example.com>

##  Add a DKIM-Filter header field to messages passing through this filter
##  to identify messages it has processed.
SoftwareHeader	yes

## SIGNING OPTIONS

##  Selects the canonicalization method(s) to be used when signing messages.
Canonicalization	relaxed/relaxed

##  Domain(s) whose mail should be signed by this filter. Mail from other domains will
##  be verified rather than being signed. Uncomment and use your domain name.
##  This parameter is not required if a SigningTable is in use.
# Domain	example.com

##  Defines the name of the selector to be used when signing messages.
Selector	default

##  Specifies the minimum number of key bits for acceptable keys and signatures.
MinimumKeyBits	1024

##  Gives the location of a private key to be used for signing ALL messages. This
##  directive is ignored if KeyTable is enabled.
KeyFile	%{_sysconfdir}/%{name}/keys/default.private

##  Gives the location of a file mapping key names to signing keys. In simple terms,
##  this tells %{upname} where to find your keys. If present, overrides any KeyFile
##  directive in the configuration file. Requires SigningTable be enabled.
# KeyTable	%{_sysconfdir}/%{name}/KeyTable

##  Defines a table used to select one or more signatures to apply to a message based
##  on the address found in the From: header field. In simple terms, this tells
##  %{upname} how to use your keys. Requires KeyTable be enabled.
# SigningTable	refile:%{_sysconfdir}/%{name}/SigningTable

##  Identifies a set of "external" hosts that may send mail through the server as one
##  of the signing domains without credentials as such.
# ExternalIgnoreList	refile:%{_sysconfdir}/%{name}/TrustedHosts

##  Identifies a set "internal" hosts whose mail should be signed rather than verified.
# InternalHosts	refile:%{_sysconfdir}/%{name}/TrustedHosts

##  Contains a list of IP addresses, CIDR blocks, hostnames or domain names
##  whose mail should be neither signed nor verified by this filter.  See man
##  page for file format.
# PeerList	X.X.X.X

##  Always oversign From (sign using actual From and a null From to prevent
##  malicious signatures header fields (From and/or others) between the signer
##  and the verifier.  From is oversigned by default in the Fedora package
##  because it is often the identity key used by reputation systems and thus
##  somewhat security sensitive.
OversignHeaders	From
EOF

%{__cat} > %{buildroot}%{_sysconfdir}/sysconfig/%{name} << 'EOF'
# Set the necessary startup options
OPTIONS="-x %{_sysconfdir}/%{name}.conf -P %{_localstatedir}/run/%{name}/%{name}.pid"

# Set the default DKIM selector
DKIM_SELECTOR=default

# Set the default DKIM key location
DKIM_KEYDIR=%{_sysconfdir}/%{name}/keys
EOF

%{__mkdir} -p %{buildroot}%{_sysconfdir}/%{name}
%{__cat} > %{buildroot}%{_sysconfdir}/%{name}/SigningTable << 'EOF'
# %{bigname} SIGNING TABLE
# This table controls how to apply one or more signatures to outgoing messages based
# on the address found in the From: header field. In simple terms, this tells
# %{upname} "how" to apply your keys.

# To use this file, uncomment the SigningTable option in %{_sysconfdir}/%{name}.conf,
# then uncomment one of the usage examples below and replace example.com with your
# domain name, then restart %{upname}.

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

%{__cat} > %{buildroot}%{_sysconfdir}/%{name}/KeyTable << 'EOF'
# %{bigname} KEY TABLE
# To use this file, uncomment the #KeyTable option in %{_sysconfdir}/%{name}.conf,
# then uncomment the following line and replace example.com with your domain
# name, then restart %{upname}. Additional keys may be added on separate lines.

#default._domainkey.example.com example.com:default:%{_sysconfdir}/%{name}/keys/default.private
EOF

%{__cat} > %{buildroot}%{_sysconfdir}/%{name}/TrustedHosts << 'EOF'
# %{bigname} TRUSTED HOSTS
# To use this file, uncomment the #ExternalIgnoreList and/or the #InternalHosts
# option in %{_sysconfdir}/%{name}.conf then restart %{upname}. Additional hosts
# may be added on separate lines (IP addresses, hostnames, or CIDR ranges).
# The localhost IP (127.0.0.1) should always be the first entry in this file.
127.0.0.1
::1
#host.example.com
#192.168.1.0/24
EOF

%{__cat} > README.fedora << 'EOF'
#####################################
#FEDORA-SPECIFIC README FOR %{bigname}#
#####################################
Last updated: Apr 30, 2015 by Steve Jenkins (steve@stevejenkins.com)

Generating keys for %{upname}
============================
After installing the %{name} package, you MUST generate a pair of keys (public and private) before
attempting to start the %{name} service.

A valid private key must exist in the location expected by %{_sysconfdir}/%{name}.conf before the service will start.

A matching public key must be included in your domain's DNS records before remote systems can validate
your outgoing mail's DKIM signature.


Generating Keys Automatically
=============================
To automatically create a pair of default keys for the local domain, do:

% sudo %{_sbindir}/%{name}-default-keygen

The default keygen script will attempt to fetch the local domain name, generate a private and public key for
the domain, then save them in %{_sysconfdir}/%{name}/keys as default.private and default.txt with the proper
ownership and permissions.

NOTE: The default key generation script MUST be run by a privileged user (or root). Otherwise, the resulting
private key ownership and permissions will not be correct.


Generating Keys Manually
========================
A privileged user (or root) can manually generate a set of keys by doing the following:

1) Create a directory to store the new keys:

% sudo mkdir %{_sysconfdir}/%{name}/keys/example.com

2) Generate keys in that directory for a specific domain name and selector:

% sudo %{_sbindir}/%{name}-genkey -D %{_sysconfdir}/%{name}/keys/example.com/ -d example.com -s default

3) Set the proper ownership for the directory and private key:

% sudo chown -R root:%{name} %{_sysconfdir}/%{name}/keys/example.com

4) Set secure permissions for the private key:

% sudo chmod 640 %{_sysconfdir}/%{name}/keys/example.com/default.private

5) Set standard permissions for the public key:

% sudo chmod 644 %{_sysconfdir}/%{name}/keys/example.com/default.txt


Updating Key Location(s) in Configuration Files
===============================================
If you run the %{name}-default-keygen script, the default keys will be saved in %{_sysconfdir}/%{name}/keys as
default.private and default.txt, which is the location expected by the default %{_sysconfdir}/%{name}.conf file.

If you manually generate your own keys, you must update the key location and name in %{_sysconfdir}/%{name}.conf
before attempting to start the %{name} service.


Using %upname with SQL Datasets
================================
%upname on RedHat-based systems relies on OpenDBX for database access. Depending on which database you use,
you may have to manually install one of the following OpenDBX subpackages (all of which are available via yum):

- opendbx-firebird
- opendbx-mssql
- opendbx-mysql
- opendbx-postgresql
- opendbx-sqlite 
- opendbx-sqlite2
- opendbx-sybase

If you have %upname configured to use SQL datasets on a systemd-based server, it might also be necessary to start
the %name service after the database servers by referencing your database unit file(s) in the "After" section of
the %upname unit file.

For example, if using both MariaDB and PostgreSQL, in %{_unitdir}/%{name}.service change:

After=network.target nss-lookup.target syslog.target

to:

After=network.target nss-lookup.target syslog.target mariadb.service postgresql.service


Additional Configuration Help
=============================
For help configuring your MTA (Postfix, Sendmail, etc.) with %{upname}, setting up DNS records with your
public DKIM key, as well as instructions on configuring %{upname} to sign outgoing mail for multiple
domains, follow the how-to at:

http://wp.me/p1iGgP-ou

Official documentation for %{upname} is available at http://%{name}.org/

%{upname} mailing lists are available at http://lists.%{name}.org/

###
EOF

%{__install} -p -d %{buildroot}%{_sysconfdir}/tmpfiles.d
%{__cat} > %{buildroot}%{_sysconfdir}/tmpfiles.d/%{name}.conf <<'EOF'
D %{_localstatedir}/run/%{name} 0700 %{name} %{name} -
EOF

%{__rm} -r %{buildroot}%{_prefix}/share/doc/%{name}
%{__rm} %{buildroot}%{_libdir}/*.a
%{__rm} %{buildroot}%{_libdir}/*.la

%{__mkdir} -p %{buildroot}%{_localstatedir}/spool/%{name}
%{__mkdir} -p %{buildroot}%{_localstatedir}/run/%{name}
%{__mkdir} -p %{buildroot}%{_sysconfdir}/%{name}
%{__mkdir} %{buildroot}%{_sysconfdir}/%{name}/keys

%{__install} -m 0755 stats/%{name}-reportstats %{buildroot}%{_prefix}/sbin/%{name}-reportstats
%{__sed} -i 's|^%{bigname}STATSDIR="/var/db/%{name}"|%{bigname}STATSDIR="%{_localstatedir}/spool/%{name}"|g' %{buildroot}%{_prefix}/sbin/%{name}-reportstats
%{__sed} -i 's|^%{bigname}DATOWNER="mailnull:mailnull"|%{bigname}DATOWNER="%{name}:%{name}"|g' %{buildroot}%{_prefix}/sbin/%{name}-reportstats

%{__chmod} 0644 contrib/convert/convert_keylist.sh

%pre
getent group %{name} >/dev/null || groupadd -r %{name}
getent passwd %{name} >/dev/null || \
	useradd -r -g %{name} -G mail -d %{_localstatedir}/run/%{name} -s /sbin/nologin \
	-c "%{upname} Milter" %{name}
exit 0

%post
%if %systemd
%systemd_post %{name}.service
%else
/sbin/chkconfig --add %{name} || :
%endif

%preun
%if %systemd
%systemd_preun %{name}.service
%else
if [ $1 -eq 0 ]; then
	service %{name} stop >/dev/null || :
	/sbin/chkconfig --del %{name} || :
fi
exit 0
%endif

%postun
%if %systemd
%systemd_postun_with_restart %{name}.service
%else
if [ "$1" -ge "1" ] ; then
	/sbin/service %{name} condrestart >/dev/null 2>&1 || :
fi
exit 0
%endif

%if %systemd
# For the switchover from initscript to service file
%triggerun -- %{name} < 2.8.0-1
%systemd_post %{name}.service
/sbin/chkconfig --del %{name} >/dev/null 2>&1 || :
%systemd_postun_with_restart %{name}.service
%endif

%post -n libopendkim -p /sbin/ldconfig

%postun -n libopendkim -p /sbin/ldconfig

%clean
%{__rm} -rf %{buildroot}

%files
%if 0%{?_licensedir:1}
%license LICENSE LICENSE.Sendmail
%else
%doc LICENSE LICENSE.Sendmail
%endif
%doc FEATURES KNOWNBUGS RELEASE_NOTES RELEASE_NOTES.Sendmail INSTALL
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
%if 0%{?_licensedir:1}
%license LICENSE LICENSE.Sendmail
%else
%doc LICENSE LICENSE.Sendmail
%endif
%doc README
%{_libdir}/lib%{name}.so.*

%files -n libopendkim-devel
%if 0%{?_licensedir:1}
%license LICENSE LICENSE.Sendmail
%else
%doc LICENSE LICENSE.Sendmail
%endif
%doc lib%{name}/docs/*.html
%{_includedir}/%{name}
%{_libdir}/*.so
%{_libdir}/pkgconfig/*.pc

%changelog
* Fri Dec 25 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.3-3
- Added OpenLDAP support for systemd branches in response to RH Bugzilla #1293279

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.10.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue May 12 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.3-1
- Updated to use newer upstream 2.10.3 source code

* Mon May 11 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.2-1
- Updated to use newer upstream 2.10.2 source code
- Removed patches for bugs fixed in upstream source
- Included support for systemd macros
- Added deprecated options notice to default configuration file
- Added new options to default configuration file
- Updated README.fedora with additional SQL useage info

* Mon Apr 13 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-13
- Obsoleted sysvinit subpackage via libopendkim subpackage
- Added more macros
- Updated README.fedora

* Mon Apr 06 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-12
- BuildRequires opendbx-devel instead of opendbx
- Fixed typo in configure flag

* Mon Apr 06 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-11
- All branches now require opendbx
- All branches now configure with --with-obdx flag
- Added comments to README.Fedora to address Bug #1209009
- Cleaned up some spacing

* Fri Apr 03 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-10
- policycoreutils now only required for EL5

* Thu Apr 02 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-9
- policycoreutils* now only required for Fedora and EL6+
- Added --with-obdx configure support for Fedora builds
- Changed a few macros
- Added additional %license support

* Sun Mar 29 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-8
- removed unecessary Requires packages
- moved libbsd back to BuildRequires
- removed unecessary %defattr
- added support for %license in place of %doc
- Changed some %{name} macro usages

* Sat Mar 28 2015 Steve Jenkins <steve@stevejenkins.com> - 2.10.1-7
- added %{?_isa} to Requires where necessary
- added sendmail-milter to Requires
- added libtool to BuildRequires
- moved libbsd from BuildRequires to Requires
- added policycoreutils and policycoreutils-python to Requires(post)

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
