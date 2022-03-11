#
# spec file for package ceph
#
# Copyright (C) 2004-2019 The Ceph Project Developers. See COPYING file
# at the top-level directory of this distribution and at
# https://github.com/ceph/ceph/blob/master/COPYING
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon.
#
# This file is under the GNU Lesser General Public License, version 2.1
#
# Please submit bugfixes or comments via http://tracker.ceph.com/
#

#################################################################################
# conditional build section
#
# please read this for explanation of bcond syntax:
# https://rpm-software-management.github.io/rpm/manual/conditionalbuilds.html
#################################################################################
%bcond_with make_check
%bcond_with zbd
%bcond_with cmake_verbose_logging
%bcond_without ceph_test_package
%ifarch s390
%bcond_with tcmalloc
%else
%bcond_without tcmalloc
%endif
%bcond_without rbd_ssd_cache
%ifarch x86_64
%bcond_without rbd_rwl_cache
%else
%bcond_with rbd_rwl_cache
%endif
%if 0%{?fedora} || 0%{?rhel}
%bcond_with system_pmdk
%bcond_without selinux
%if 0%{?rhel} >= 8
%bcond_with cephfs_java
%else
%bcond_without cephfs_java
%endif
%bcond_without amqp_endpoint
%bcond_without kafka_endpoint
%bcond_without lttng
%bcond_without libradosstriper
%bcond_without ocf
%global luarocks_package_name luarocks
%bcond_without lua_packages
%global _remote_tarball_prefix https://download.ceph.com/tarballs/
%endif
%if 0%{?suse_version}
%bcond_without system_pmdk
%bcond_with amqp_endpoint
%bcond_with cephfs_java
%bcond_with kafka_endpoint
%bcond_with libradosstriper
%ifarch x86_64 aarch64 ppc64le
%bcond_without lttng
%else
%bcond_with lttng
%endif
%bcond_with ocf
%bcond_with selinux
#Compat macro for _fillupdir macro introduced in Nov 2017
%if ! %{defined _fillupdir}
%global _fillupdir /var/adm/fillup-templates
%endif
#luarocks
%if 0%{?is_opensuse}
# openSUSE
%bcond_without lua_packages
%if 0%{?sle_version}
# openSUSE Leap
%global luarocks_package_name lua53-luarocks
%else
# openSUSE Tumbleweed
%global luarocks_package_name lua54-luarocks
%endif
%else
# SLE
%bcond_with lua_packages
%endif
%endif
%bcond_with seastar
%bcond_with jaeger
%if 0%{?fedora} || 0%{?suse_version} >= 1500
# distros that ship cmd2 and/or colorama
%bcond_without cephfs_shell
%else
# distros that do _not_ ship cmd2/colorama
%bcond_with cephfs_shell
%endif
%if 0%{?fedora} || 0%{?suse_version} || 0%{?rhel} >= 8
%global weak_deps 1
%endif
%if %{with selinux}
# get selinux policy version
# Force 0.0.0 policy version for centos builds to avoid repository sync issues between rhel and centos
%if 0%{?centos}
%global _selinux_policy_version 0.0.0
%else
%{!?_selinux_policy_version: %global _selinux_policy_version 0.0.0}
%endif
%endif

%{!?_udevrulesdir: %global _udevrulesdir /lib/udev/rules.d}
%{!?tmpfiles_create: %global tmpfiles_create systemd-tmpfiles --create}
%{!?python3_pkgversion: %global python3_pkgversion 3}
%{!?python3_version_nodots: %global python3_version_nodots 3}
%{!?python3_version: %global python3_version 3}

%if ! 0%{?suse_version}
# use multi-threaded xz compression: xz level 7 using ncpus threads
%global _source_payload w7T%{_smp_build_ncpus}.xzdio
%global _binary_payload w7T%{_smp_build_ncpus}.xzdio
%endif

%define smp_limit_mem_per_job() %( \
  kb_per_job=%1 \
  kb_total=$(head -3 /proc/meminfo | sed -n 's/MemAvailable:\\s*\\(.*\\) kB.*/\\1/p') \
  jobs=$(( $kb_total / $kb_per_job )) \
  [ $jobs -lt 1 ] && jobs=1 \
  echo $jobs )

%if 0%{?_smp_ncpus_max} == 0
%if 0%{?__isa_bits} == 32
# 32-bit builds can use 3G memory max, which is not enough even for -j2
%global _smp_ncpus_max 1
%else
# 3.0 GiB mem per job
# SUSE distros use limit_build in the place of smp_limit_mem_per_job, please
# be sure to update it (in the build section, below) as well when changing this
# number.
%global _smp_ncpus_max %{smp_limit_mem_per_job 3000000}
%endif
%endif

#################################################################################
# main package definition
#################################################################################
Name:		ceph
Version:	17.0.0
Release:	10266.gd581ba839ed%{?dist}
%if 0%{?fedora} || 0%{?rhel}
Epoch:		2
%endif

# define _epoch_prefix macro which will expand to the empty string if epoch is
# undefined
%global _epoch_prefix %{?epoch:%{epoch}:}

Summary:	User space components of the Ceph file system
License:	LGPL-2.1 and LGPL-3.0 and CC-BY-SA-3.0 and GPL-2.0 and BSL-1.0 and BSD-3-Clause and MIT
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
URL:		http://ceph.com/
Source0:	%{?_remote_tarball_prefix}ceph-17.0.0-10266-gd581ba839ed.tar.bz2
%if 0%{?suse_version}
# _insert_obs_source_lines_here
ExclusiveArch:  x86_64 aarch64 ppc64le s390x
%endif
#################################################################################
# dependencies that apply across all distro families
#################################################################################
Requires:       ceph-osd = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-mds = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-mgr = %{_epoch_prefix}%{version}-%{release}
Requires:       ceph-mon = %{_epoch_prefix}%{version}-%{release}
Requires(post):	binutils
%if 0%{with cephfs_java}
BuildRequires:	java-devel
BuildRequires:	sharutils
%endif
%if 0%{with selinux}
BuildRequires:	checkpolicy
BuildRequires:	selinux-policy-devel
%endif
BuildRequires:	gperf
BuildRequires:  cmake > 3.5
BuildRequires:	fuse-devel
%if 0%{with seastar} && 0%{?rhel}
BuildRequires:	gcc-toolset-9-gcc-c++ >= 9.2.1-2.3
%else
BuildRequires:	gcc-c++
%endif
%if 0%{with tcmalloc}
# libprofiler did not build on ppc64le until 2.7.90
%if 0%{?fedora} || 0%{?rhel} >= 8
BuildRequires:	gperftools-devel >= 2.7.90
%endif
%if 0%{?rhel} && 0%{?rhel} < 8
BuildRequires:	gperftools-devel >= 2.6.1
%endif
%if 0%{?suse_version}
BuildRequires:	gperftools-devel >= 2.4
%endif
%endif
BuildRequires:	libaio-devel
BuildRequires:	libblkid-devel >= 2.17
BuildRequires:	cryptsetup-devel
BuildRequires:	libcurl-devel
BuildRequires:	libcap-ng-devel
BuildRequires:	fmt-devel >= 6.2.1
BuildRequires:	pkgconfig(libudev)
BuildRequires:	libnl3-devel
BuildRequires:	liboath-devel
BuildRequires:	libtool
BuildRequires:	libxml2-devel
BuildRequires:	make
BuildRequires:	ncurses-devel
BuildRequires:	libicu-devel
BuildRequires:	patch
BuildRequires:	perl
BuildRequires:	pkgconfig
BuildRequires:  procps
BuildRequires:	python%{python3_pkgversion}
BuildRequires:	python%{python3_pkgversion}-devel
BuildRequires:	python%{python3_pkgversion}-setuptools
BuildRequires:	python%{python3_pkgversion}-Cython
BuildRequires:	snappy-devel
BuildRequires:	sqlite-devel
BuildRequires:	sudo
BuildRequires:	pkgconfig(udev)
BuildRequires:	valgrind-devel
BuildRequires:	which
BuildRequires:	xfsprogs-devel
BuildRequires:	xmlstarlet
BuildRequires:	nasm
BuildRequires:	lua-devel
%if 0%{with seastar} || 0%{with jaeger}
BuildRequires:  yaml-cpp-devel >= 0.6
%endif
%if 0%{with amqp_endpoint}
BuildRequires:  librabbitmq-devel
%endif
%if 0%{with kafka_endpoint}
BuildRequires:  librdkafka-devel
%endif
%if 0%{with lua_packages}
BuildRequires:  %{luarocks_package_name}
%endif
%if 0%{with make_check}
BuildRequires:  hostname
BuildRequires:  jq
BuildRequires:	libuuid-devel
BuildRequires:	python%{python3_pkgversion}-bcrypt
BuildRequires:	python%{python3_pkgversion}-nose
BuildRequires:	python%{python3_pkgversion}-pecan
BuildRequires:	python%{python3_pkgversion}-requests
BuildRequires:	python%{python3_pkgversion}-dateutil
BuildRequires:	python%{python3_pkgversion}-coverage
BuildRequires:	python%{python3_pkgversion}-pyOpenSSL
BuildRequires:	socat
%endif
%if 0%{with zbd}
BuildRequires:  libzbd-devel
%endif
%if 0%{with jaeger}
BuildRequires:  bison
BuildRequires:  flex
BuildRequires:  thrift-devel >= 0.13.0
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:  json-devel
%endif
%if 0%{?suse_version}
BuildRequires:  nlohmann_json-devel
%endif
BuildRequires:  libevent-devel
%endif
%if 0%{with system_pmdk}
BuildRequires:  libpmem-devel
BuildRequires:  libpmemobj-devel
%endif
%if 0%{with seastar}
BuildRequires:  c-ares-devel
BuildRequires:  gnutls-devel
BuildRequires:  hwloc-devel
BuildRequires:  libpciaccess-devel
BuildRequires:  lksctp-tools-devel
BuildRequires:  ragel
BuildRequires:  systemtap-sdt-devel
%if 0%{?fedora}
BuildRequires:  libubsan
BuildRequires:  libasan
BuildRequires:  libatomic
%endif
%if 0%{?rhel}
BuildRequires:  gcc-toolset-9-annobin
BuildRequires:  gcc-toolset-9-libubsan-devel
BuildRequires:  gcc-toolset-9-libasan-devel
BuildRequires:  gcc-toolset-9-libatomic-devel
%endif
%endif
#################################################################################
# distro-conditional dependencies
#################################################################################
%if 0%{?suse_version}
BuildRequires:  pkgconfig(systemd)
BuildRequires:	systemd-rpm-macros
%{?systemd_requires}
PreReq:		%fillup_prereq
BuildRequires:	fdupes
BuildRequires:  memory-constraints
BuildRequires:	net-tools
BuildRequires:	libbz2-devel
BuildRequires:	mozilla-nss-devel
BuildRequires:	keyutils-devel
BuildRequires:  libopenssl-devel
BuildRequires:  openldap2-devel
#BuildRequires:  krb5
#BuildRequires:  krb5-devel
BuildRequires:  cunit-devel
BuildRequires:	python%{python3_pkgversion}-PrettyTable
BuildRequires:	python%{python3_pkgversion}-PyYAML
BuildRequires:	python%{python3_pkgversion}-Sphinx
BuildRequires:  rdma-core-devel
BuildRequires:	liblz4-devel >= 1.7
# for prometheus-alerts
BuildRequires:  golang-github-prometheus-prometheus
%endif
%if 0%{?fedora} || 0%{?rhel}
Requires:	systemd
BuildRequires:  boost-random
BuildRequires:	nss-devel
BuildRequires:	keyutils-libs-devel
BuildRequires:	libibverbs-devel
BuildRequires:  librdmacm-devel
BuildRequires:  openldap-devel
#BuildRequires:  krb5-devel
BuildRequires:  openssl-devel
BuildRequires:  CUnit-devel
BuildRequires:	python%{python3_pkgversion}-devel
BuildRequires:	python%{python3_pkgversion}-prettytable
BuildRequires:	python%{python3_pkgversion}-pyyaml
BuildRequires:	python%{python3_pkgversion}-sphinx
BuildRequires:	lz4-devel >= 1.7
%endif
# distro-conditional make check dependencies
%if 0%{with make_check}
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:	golang-github-prometheus
BuildRequires:	jsonnet
BuildRequires:	libtool-ltdl-devel
BuildRequires:	ninja-build
BuildRequires:	xmlsec1
BuildRequires:	xmlsec1-devel
%ifarch x86_64
BuildRequires:	xmlsec1-nss
%endif
BuildRequires:	xmlsec1-openssl
BuildRequires:	xmlsec1-openssl-devel
BuildRequires:	python%{python3_pkgversion}-cherrypy
BuildRequires:	python%{python3_pkgversion}-jwt
BuildRequires:	python%{python3_pkgversion}-routes
BuildRequires:	python%{python3_pkgversion}-scipy
BuildRequires:	python%{python3_pkgversion}-werkzeug
BuildRequires:	python%{python3_pkgversion}-pyOpenSSL
%endif
%if 0%{?suse_version}
BuildRequires:	golang-github-prometheus-prometheus
BuildRequires:	jsonnet
BuildRequires:	libxmlsec1-1
BuildRequires:	libxmlsec1-nss1
BuildRequires:	libxmlsec1-openssl1
BuildRequires:	ninja
BuildRequires:	python%{python3_pkgversion}-CherryPy
BuildRequires:	python%{python3_pkgversion}-PyJWT
BuildRequires:	python%{python3_pkgversion}-Routes
BuildRequires:	python%{python3_pkgversion}-Werkzeug
BuildRequires:	python%{python3_pkgversion}-numpy-devel
BuildRequires:	xmlsec1-devel
BuildRequires:	xmlsec1-openssl-devel
%endif
%endif
# lttng and babeltrace for rbd-replay-prep
%if %{with lttng}
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:	lttng-ust-devel
BuildRequires:	libbabeltrace-devel
%endif
%if 0%{?suse_version}
BuildRequires:	lttng-ust-devel
BuildRequires:  babeltrace-devel
%endif
%endif
%if 0%{?suse_version}
BuildRequires:	libexpat-devel
%endif
%if 0%{?rhel} || 0%{?fedora}
BuildRequires:	expat-devel
%endif
#hardened-cc1
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:  redhat-rpm-config
%endif
%if 0%{with seastar}
%if 0%{?fedora} || 0%{?rhel}
BuildRequires:  cryptopp-devel
BuildRequires:  numactl-devel
%endif
%if 0%{?suse_version}
BuildRequires:  libcryptopp-devel
BuildRequires:  libnuma-devel
%endif
%endif
%if 0%{?rhel} >= 8
BuildRequires:  /usr/bin/pathfix.py
%endif

%description
Ceph is a massively scalable, open-source, distributed storage system that runs
on commodity hardware and delivers object, block and file system storage.


#################################################################################
# subpackages
#################################################################################
%package base
Summary:       Ceph Base Package
%if 0%{?suse_version}
Group:         System/Filesystems
%endif
Provides:      ceph-test:/usr/bin/ceph-kvstore-tool
Requires:      ceph-common = %{_epoch_prefix}%{version}-%{release}
Requires:      librbd1 = %{_epoch_prefix}%{version}-%{release}
Requires:      librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:      libcephfs2 = %{_epoch_prefix}%{version}-%{release}
Requires:      librgw2 = %{_epoch_prefix}%{version}-%{release}
%if 0%{with selinux}
Requires:      ceph-selinux = %{_epoch_prefix}%{version}-%{release}
%endif
Requires:      findutils
Requires:      grep
Requires:      logrotate
Requires:      psmisc
Requires:      util-linux
Requires:      which
%if 0%{?rhel} && 0%{?rhel} < 8
# The following is necessary due to tracker 36508 and can be removed once the
# associated upstream bugs are resolved.
%if 0%{with tcmalloc}
Requires:      gperftools-libs >= 2.6.1
%endif
%endif
%if 0%{?weak_deps}
Recommends:    chrony
Recommends:    nvme-cli
%if 0%{?suse_version}
Requires:      smartmontools
%else
Recommends:    smartmontools
%endif
%endif
%description base
Base is the package that includes all the files shared amongst ceph servers

%package -n ceph-common
Summary:	Ceph Common
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	libcephfs2 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rbd = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-cephfs = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rgw = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-ceph-argparse = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-ceph-common = %{_epoch_prefix}%{version}-%{release}
%if 0%{?fedora} || 0%{?rhel}
Requires:	python%{python3_pkgversion}-prettytable
%endif
%if 0%{?suse_version}
Requires:	python%{python3_pkgversion}-PrettyTable
%endif
%if 0%{with libradosstriper}
Requires:	libradosstriper1 = %{_epoch_prefix}%{version}-%{release}
%endif
%{?systemd_requires}
%if 0%{?suse_version}
Requires(pre):	pwdutils
%endif
%description -n ceph-common
Common utilities to mount and interact with a ceph storage cluster.
Comprised of files that are common to Ceph clients and servers.

%package radosgw
Summary:	Rados REST gateway
%if 0%{?suse_version}
Group:		System/Filesystems
%endif
Requires:	ceph-base = %{_epoch_prefix}%{version}-%{release}
%if 0%{with selinux}
Requires:	ceph-selinux = %{_epoch_prefix}%{version}-%{release}
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
Requires:	librgw2 = %{_epoch_prefix}%{version}-%{release}
%if 0%{?rhel} || 0%{?fedora}
Requires:	mailcap
%endif
%if 0%{?weak_deps}
Recommends:	gawk
%endif
%description radosgw
RADOS is a distributed object store used by the Ceph distributed
storage system.  This package provides a REST gateway to the
object store that aims to implement a superset of Amazon's S3
service as well as the OpenStack Object Storage ("Swift") API.

%package -n librados2
Summary:	RADOS distributed object store client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{_epoch_prefix}%{version}-%{release}
%endif
%description -n librados2
RADOS is a reliable, autonomic distributed object storage cluster
developed as part of the Ceph distributed storage system. This is a
shared library allowing applications to access the distributed object
store using a simple file-like interface.

%package -n librgw2
Summary:	RADOS gateway client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%description -n librgw2
This package provides a library implementation of the RADOS gateway
(distributed object store with S3 and Swift personalities).

%package -n python%{python3_pkgversion}-rgw
Summary:	Python 3 libraries for the RADOS gateway
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	librgw2 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-rgw}
Provides:	python-rgw = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-rgw < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-rgw
This package contains Python 3 libraries for interacting with Ceph RADOS
gateway.

%package -n python%{python3_pkgversion}-rados
Summary:	Python 3 libraries for the RADOS object store
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	python%{python3_pkgversion}
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-rados}
Provides:	python-rados = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-rados < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-rados
This package contains Python 3 libraries for interacting with Ceph RADOS
object store.

%if 0%{with libradosstriper}
%package -n libradosstriper1
Summary:	RADOS striping interface
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%description -n libradosstriper1
Striping interface built on top of the rados library, allowing
to stripe bigger objects onto several standard rados objects using
an interface very similar to the rados one.
%endif

%package -n librbd1
Summary:	RADOS block device client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Requires:	librados2 = %{_epoch_prefix}%{version}-%{release}
%if 0%{?suse_version}
Requires(post): coreutils
%endif
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{_epoch_prefix}%{version}-%{release}
%endif
%description -n librbd1
RBD is a block device striped across multiple distributed objects in
RADOS, a reliable, autonomic distributed object storage cluster
developed as part of the Ceph distributed storage system. This is a
shared library allowing applications to manage these block devices.

%package -n python%{python3_pkgversion}-rbd
Summary:	Python 3 libraries for the RADOS block device
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	librbd1 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-rbd}
Provides:	python-rbd = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-rbd < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-rbd
This package contains Python 3 libraries for interacting with Ceph RADOS
block device.

%package -n libcephfs2
Summary:	Ceph distributed file system client library
%if 0%{?suse_version}
Group:		System/Libraries
%endif
Obsoletes:	libcephfs1 < %{_epoch_prefix}%{version}-%{release}
%if 0%{?rhel} || 0%{?fedora}
Obsoletes:	ceph-libs < %{_epoch_prefix}%{version}-%{release}
Obsoletes:	ceph-libcephfs
%endif
%description -n libcephfs2
Ceph is a distributed network file system designed to provide excellent
performance, reliability, and scalability. This is a shared library
allowing applications to access a Ceph distributed file system via a
POSIX-like interface.

%package -n python%{python3_pkgversion}-cephfs
Summary:	Python 3 libraries for Ceph distributed file system
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
Requires:	libcephfs2 = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-rados = %{_epoch_prefix}%{version}-%{release}
Requires:	python%{python3_pkgversion}-ceph-argparse = %{_epoch_prefix}%{version}-%{release}
%{?python_provide:%python_provide python%{python3_pkgversion}-cephfs}
Provides:	python-cephfs = %{_epoch_prefix}%{version}-%{release}
Obsoletes:	python-cephfs < %{_epoch_prefix}%{version}-%{release}
%description -n python%{python3_pkgversion}-cephfs
This package contains Python 3 libraries for interacting with Ceph distributed
file system.

%package -n python%{python3_pkgversion}-ceph-argparse
Summary:	Python 3 utility libraries for Ceph CLI
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
%{?python_provide:%python_provide python%{python3_pkgversion}-ceph-argparse}
%description -n python%{python3_pkgversion}-ceph-argparse
This package contains types and routines for Python 3 used by the Ceph CLI as
well as the RESTful interface. These have to do with querying the daemons for
command-description information, validating user command input against those
descriptions, and submitting the command to the appropriate daemon.

%package -n python%{python3_pkgversion}-ceph-common
Summary:	Python 3 utility libraries for Ceph
%if 0%{?fedora} || 0%{?rhel} >= 8
Requires:       python%{python3_pkgversion}-pyyaml
%endif
%if 0%{?suse_version}
Requires:       python%{python3_pkgversion}-PyYAML
%endif
%if 0%{?suse_version}
Group:		Development/Libraries/Python
%endif
%{?python_provide:%python_provide python%{python3_pkgversion}-ceph-common}
%description -n python%{python3_pkgversion}-ceph-common
This package contains data structures, classes and functions used by Ceph.
It also contains utilities used for the cephadm orchestrator.

#################################################################################
# common
#################################################################################
%prep
%autosetup -p1 -n ceph-17.0.0-10266-gd581ba839ed

%build
# Disable lto on systems that do not support symver attribute
# See https://gcc.gnu.org/bugzilla/show_bug.cgi?id=48200 for details
%if ( 0%{?rhel} && 0%{?rhel} < 9 ) || ( 0%{?suse_version} && 0%{?suse_version} <= 1500 )
%define _lto_cflags %{nil}
%endif

%if 0%{with seastar} && 0%{?rhel}
. /opt/rh/gcc-toolset-9/enable
%endif

%if 0%{with cephfs_java}
# Find jni.h
for i in /usr/{lib64,lib}/jvm/java/include{,/linux}; do
    [ -d $i ] && java_inc="$java_inc -I$i"
done
%endif

%if 0%{?suse_version}
%limit_build -m 3000
%endif

export CPPFLAGS="$java_inc"
export CFLAGS="$RPM_OPT_FLAGS"
export CXXFLAGS="$RPM_OPT_FLAGS"
export LDFLAGS="$RPM_LD_FLAGS"

%if 0%{with seastar}
# seastar uses longjmp() to implement coroutine. and this annoys longjmp_chk()
export CXXFLAGS=$(echo $RPM_OPT_FLAGS | sed -e 's/-Wp,-D_FORTIFY_SOURCE=2//g')
%endif

env | sort

%{?!_vpath_builddir:%global _vpath_builddir %{_target_platform}}

# TODO: drop this step once we can use `cmake -B`
mkdir -p %{_vpath_builddir}
pushd %{_vpath_builddir}
cmake .. \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DCMAKE_INSTALL_LIBDIR:PATH=%{_libdir} \
    -DCMAKE_INSTALL_LIBEXECDIR:PATH=%{_libexecdir} \
    -DCMAKE_INSTALL_LOCALSTATEDIR:PATH=%{_localstatedir} \
    -DCMAKE_INSTALL_SYSCONFDIR:PATH=%{_sysconfdir} \
    -DCMAKE_INSTALL_MANDIR:PATH=%{_mandir} \
    -DCMAKE_INSTALL_DOCDIR:PATH=%{_docdir}/ceph \
    -DCMAKE_INSTALL_INCLUDEDIR:PATH=%{_includedir} \
    -DSYSTEMD_SYSTEM_UNIT_DIR:PATH=%{_unitdir} \
    -DWITH_MANPAGE:BOOL=ON \
    -DWITH_PYTHON3:STRING=%{python3_version} \
    -DWITH_MGR_DASHBOARD_FRONTEND:BOOL=OFF \
    -DWITH_ASAN:BOOL=OFF \
    -DWITH_ASAN_LEAK:BOOL=OFF \
    -DBUILD_GMOCK:BOOL=OFF \
    -DDEBUG_GATHER:BOOL=OFF \
    -DDIAGNOSTICS_COLOR:STRING=auto \
    -DENABLE_COVERAGE:BOOL=OFF \
    -DWITH_BLKIN:BOOL=OFF \
    -DINSTALL_GTEST:BOOL=OFF \
    -DPG_DEBUG_REFS:BOOL=OFF \
    -DWITH_BLUEFS:BOOL=OFF \
    -DUSE_SQLITE:BOOL=OFF \
    -DWITH_BOOST_VALGRIND:BOOL=OFF \
    -DWITH_BROTLI:BOOL=OFF \
    -DWITH_CCACHE:BOOL=OFF \
    -DWITH_CEPHFS_TOP:BOOL=OFF \
    -DWITH_DMCLOCK_TESTS:BOOL=OFF \
    -DWITH_CEPH_DEBUG_MUTEX:BOOL=OFF \
    -DWITH_DOKAN:BOOL=OFF \
    -DWITH_FIO:BOOL=OFF \
    -DWITH_FUSE:BOOL=OFF \
    -DWITH_GRAFANA:BOOL=OFF \
    -DWITH_GSSAPI:BOOL=OFF \
    -DWITH_GTEST_PARALLEL:BOOL=OFF \
    -DWITH_LIBCEPHSQLITE:BOOL=OFF \
    -DWITH_LZ4:BOOL=OFF \
    -DWITH_MGR:BOOL=OFF \
    -DWITH_MGR_ROOK_CLIENT:BOOL=OFF \
    -DWITH_OPENLDAP:BOOL=OFF \
    -DWITH_OSD_INSTRUMENT_FUNCTIONS:BOOL=OFF \
    -DWITH_PROFILER:BOOL=OFF\
    -DWITH_OPENLDAP:BOOL=OFF \
    -DWITH_QATZIP:BOOL=OFF \
    -DWITH_RDMA:BOOL=OFF \
    -DWITH_SPDK:BOOL=OFF \
    -DWITH_SYSTEM_BOOST:BOOL=OFF \
    -DWITH_SYSTEM_GTEST:BOOL=OFF \
    -DWITH_SYSTEM_ROCKSDB:BOOL=OFF \
    -DWITH_SYSTEM_NPM:BOOL=OFF \
    -DWITH_LIBURING:BOOL=OFF \
    -Ddmclock_TEST:BOOL=OFF \
    -Dgmock_build_tests:BOOL=OFF \
    -Dgtest_build_samples:BOOL=OFF \
    -Dgtest_build_tests:BOOL=OFF \
    -Dgtest_disable_pthreads:BOOL=OFF \
    -DWITH_DPDK:BOOL=OFF \
    -DWITH_TSAN:BOOL=OFF \
    -DWITH_UBSAN:BOOL=OFF \
    -Dgtest_hide_internal_symbols:BOOL=OFF \
    -DWITH_SYSTEM_ZSTD:BOOL=OFF \
    -DWITH_KVS:BOOL=OFF \
    -DWITH_RBD:BOOL=ON \
    -DWITH_XFS:BOOL=OFF \
    -DWITH_ZBD:BOOL=OFF \
    -DWITH_ZFS:BOOL=OFF \
    -DWITH_KRBD:BOOL=OFF \
    -DWITH_LIBCEPHFS:BOOL=ON \
    -DWITH_RADOSGW_DBSTORE:BOOL=OFF \
%if 0%{without ceph_test_package}
    -DWITH_TESTS:BOOL=OFF \
%endif
%if 0%{with cephfs_java}
    -DWITH_CEPHFS_JAVA:BOOL=ON \
%endif
%if 0%{with selinux}
    -DWITH_SELINUX:BOOL=ON \
%endif
%if %{with lttng}
    -DWITH_LTTNG:BOOL=ON \
    -DWITH_BABELTRACE:BOOL=ON \
%else
    -DWITH_LTTNG:BOOL=OFF \
    -DWITH_BABELTRACE:BOOL=OFF \
%endif
    $CEPH_EXTRA_CMAKE_ARGS \
%if 0%{with ocf}
    -DWITH_OCF:BOOL=ON \
%endif
%if 0%{with cephfs_shell}
    -DWITH_CEPHFS_SHELL:BOOL=ON \
%endif
%if 0%{with libradosstriper}
    -DWITH_LIBRADOSSTRIPER:BOOL=ON \
%else
    -DWITH_LIBRADOSSTRIPER:BOOL=OFF \
%endif
%if 0%{with amqp_endpoint}
    -DWITH_RADOSGW_AMQP_ENDPOINT:BOOL=ON \
%else
    -DWITH_RADOSGW_AMQP_ENDPOINT:BOOL=OFF \
%endif
%if 0%{with kafka_endpoint}
    -DWITH_RADOSGW_KAFKA_ENDPOINT:BOOL=ON \
%else
    -DWITH_RADOSGW_KAFKA_ENDPOINT:BOOL=OFF \
%endif
%if 0%{without lua_packages}
    -DWITH_RADOSGW_LUA_PACKAGES:BOOL=OFF \
%endif
%if 0%{with zbd}
    -DWITH_ZBD:BOOL=ON \
%endif
%if 0%{with cmake_verbose_logging}
    -DCMAKE_VERBOSE_MAKEFILE:BOOL=ON \
%endif
%if 0%{with rbd_rwl_cache}
    -DWITH_RBD_RWL:BOOL=ON \
%endif
%if 0%{with rbd_ssd_cache}
    -DWITH_RBD_SSD_CACHE:BOOL=ON \
%endif
%if 0%{with system_pmdk}
    -DWITH_SYSTEM_PMDK:BOOL=ON \
%endif
%if 0%{with jaeger}
    -DWITH_JAEGER:BOOL=ON \
%endif
%if 0%{?suse_version}
    -DBOOST_J:STRING=%{jobs} \
%else
    -DBOOST_J:STRING=%{_smp_build_ncpus} \
%endif
%if 0%{?rhel}
    -DWITH_FMT_HEADER_ONLY:BOOL=ON \
%endif
    -DWITH_GRAFANA:BOOL=OFF

%if %{with cmake_verbose_logging}
cat ./CMakeFiles/CMakeOutput.log
cat ./CMakeFiles/CMakeError.log
%endif

%if 0%{?suse_version}
make %{_smp_mflags}
%else
%make_build
%endif

popd

%if 0%{with make_check}
%check
# run in-tree unittests
pushd %{_vpath_builddir}
ctest %{_smp_mflags}
popd
%endif


%install
pushd %{_vpath_builddir}
%make_install
# we have dropped sysvinit bits
rm -f %{buildroot}/%{_sysconfdir}/init.d/ceph
popd

%if 0%{with seastar}
# package crimson-osd with the name of ceph-osd
install -m 0755 %{buildroot}%{_bindir}/crimson-osd %{buildroot}%{_bindir}/ceph-osd
%endif

install -m 0644 -D src/etc-rbdmap %{buildroot}%{_sysconfdir}/ceph/rbdmap
%if 0%{?fedora} || 0%{?rhel}
install -m 0644 -D etc/sysconfig/ceph %{buildroot}%{_sysconfdir}/sysconfig/ceph
%endif
%if 0%{?suse_version}
install -m 0644 -D etc/sysconfig/ceph %{buildroot}%{_fillupdir}/sysconfig.%{name}
%endif
install -m 0644 -D systemd/ceph.tmpfiles.d %{buildroot}%{_tmpfilesdir}/ceph-common.conf
install -m 0644 -D systemd/50-ceph.preset %{buildroot}%{_presetdir}/50-ceph.preset
mkdir -p %{buildroot}%{_sbindir}
install -m 0644 -D src/logrotate.conf %{buildroot}%{_sysconfdir}/logrotate.d/ceph
chmod 0644 %{buildroot}%{_docdir}/ceph/sample.ceph.conf
install -m 0644 -D COPYING %{buildroot}%{_docdir}/ceph/COPYING
install -m 0644 -D etc/sysctl/90-ceph-osd.conf %{buildroot}%{_sysctldir}/90-ceph-osd.conf
install -m 0755 -D src/tools/rbd_nbd/rbd-nbd_quiesce %{buildroot}%{_libexecdir}/rbd-nbd/rbd-nbd_quiesce

install -m 0755 src/cephadm/cephadm %{buildroot}%{_sbindir}/cephadm
mkdir -p %{buildroot}%{_sharedstatedir}/cephadm
chmod 0700 %{buildroot}%{_sharedstatedir}/cephadm
mkdir -p %{buildroot}%{_sharedstatedir}/cephadm/.ssh
chmod 0700 %{buildroot}%{_sharedstatedir}/cephadm/.ssh
touch %{buildroot}%{_sharedstatedir}/cephadm/.ssh/authorized_keys
chmod 0600 %{buildroot}%{_sharedstatedir}/cephadm/.ssh/authorized_keys

# firewall templates and /sbin/mount.ceph symlink
%if 0%{?suse_version} && !0%{?usrmerged}
mkdir -p %{buildroot}/sbin
ln -sf %{_sbindir}/mount.ceph %{buildroot}/sbin/mount.ceph
%endif

# udev rules
install -m 0644 -D udev/50-rbd.rules %{buildroot}%{_udevrulesdir}/50-rbd.rules

# sudoers.d
install -m 0440 -D sudoers.d/ceph-smartctl %{buildroot}%{_sysconfdir}/sudoers.d/ceph-smartctl

%if 0%{?rhel} >= 8
pathfix.py -pni "%{__python3} %{py3_shbang_opts}" %{buildroot}%{_bindir}/*
pathfix.py -pni "%{__python3} %{py3_shbang_opts}" %{buildroot}%{_sbindir}/*
%endif

#set up placeholder directories
mkdir -p %{buildroot}%{_sysconfdir}/ceph
mkdir -p %{buildroot}%{_localstatedir}/run/ceph
mkdir -p %{buildroot}%{_localstatedir}/log/ceph
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/tmp
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/mon
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/osd
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/mds
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/mgr
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/crash
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/crash/posted
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/radosgw
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-osd
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-mds
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-rgw
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-mgr
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-rbd
mkdir -p %{buildroot}%{_localstatedir}/lib/ceph/bootstrap-rbd-mirror

# prometheus alerts
install -m 644 -D monitoring/prometheus/alerts/ceph_default_alerts.yml %{buildroot}/etc/prometheus/ceph/ceph_default_alerts.yml

%if 0%{?suse_version}
# create __pycache__ directories and their contents
%py3_compile %{buildroot}%{python3_sitelib}
# hardlink duplicate files under /usr to save space
%fdupes %{buildroot}%{_prefix}
%endif

%if 0%{?rhel} == 8
%py_byte_compile %{__python3} %{buildroot}%{python3_sitelib}
%endif

%clean
rm -rf %{buildroot}

#################################################################################
# files and systemd scriptlets
#################################################################################
%files

%files base
%{_bindir}/ceph-crash
%{_bindir}/crushtool
%{_bindir}/monmaptool
%{_bindir}/osdmaptool
%{_bindir}/ceph-kvstore-tool
%{_bindir}/ceph-run
%{_presetdir}/50-ceph.preset
%{_sbindir}/ceph-create-keys
%dir %{_libexecdir}/ceph
%{_libexecdir}/ceph/ceph_common.sh
%dir %{_libdir}/rados-classes
%{_libdir}/rados-classes/*
%dir %{_libdir}/ceph
%dir %{_libdir}/ceph/erasure-code
%{_libdir}/ceph/erasure-code/libec_*.so*
%dir %{_libdir}/ceph/compressor
%{_libdir}/ceph/compressor/libceph_*.so*
%{_unitdir}/ceph-crash.service
%dir %{_libdir}/ceph/crypto
%{_libdir}/ceph/crypto/libceph_*.so*
%if %{with lttng}
%{_libdir}/libos_tp.so*
%{_libdir}/libosd_tp.so*
%endif
%config(noreplace) %{_sysconfdir}/logrotate.d/ceph
%if 0%{?fedora} || 0%{?rhel}
%config(noreplace) %{_sysconfdir}/sysconfig/ceph
%endif
%if 0%{?suse_version}
%{_fillupdir}/sysconfig.*
%endif
%{_unitdir}/ceph.target
%{_mandir}/man8/ceph-create-keys.8*
%{_mandir}/man8/ceph-run.8*
%{_mandir}/man8/crushtool.8*
%{_mandir}/man8/osdmaptool.8*
%{_mandir}/man8/monmaptool.8*
%{_mandir}/man8/ceph-kvstore-tool.8*
#set up placeholder directories
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/crash
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/crash/posted
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/tmp
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-osd
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-mds
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-rgw
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-mgr
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-rbd
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/bootstrap-rbd-mirror
%{_sysconfdir}/sudoers.d/ceph-smartctl

%post base
/sbin/ldconfig
%if 0%{?suse_version}
%fillup_only
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl preset ceph.target ceph-crash.service >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph.target ceph-crash.service
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph.target ceph-crash.service >/dev/null 2>&1 || :
fi

%preun base
%if 0%{?suse_version}
%service_del_preun ceph.target ceph-crash.service
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph.target ceph-crash.service
%endif

%postun base
/sbin/ldconfig
%systemd_postun ceph.target

%files common
%dir %{_docdir}/ceph
%doc %{_docdir}/ceph/sample.ceph.conf
%license %{_docdir}/ceph/COPYING
%{_bindir}/ceph
%{_bindir}/ceph-authtool
%{_bindir}/ceph-conf
%{_bindir}/ceph-dencoder
%{_bindir}/ceph-rbdnamer
%{_bindir}/ceph-syn
%{_bindir}/cephfs-data-scan
%{_bindir}/cephfs-journal-tool
%{_bindir}/cephfs-table-tool
%{_bindir}/crushdiff
%{_bindir}/rados
%{_bindir}/radosgw-admin
%{_bindir}/rbd
%{_bindir}/rbd-replay
%{_bindir}/rbd-replay-many
%{_bindir}/rbdmap
%{_sbindir}/mount.ceph
%if 0%{?suse_version} && !0%{?usrmerged}
/sbin/mount.ceph
%endif
%if %{with lttng}
%{_bindir}/rbd-replay-prep
%endif
%{_bindir}/ceph-post-file
%dir %{_libdir}/ceph/denc
%{_libdir}/ceph/denc/denc-mod-*.so
%{_tmpfilesdir}/ceph-common.conf
%{_mandir}/man8/ceph-authtool.8*
%{_mandir}/man8/ceph-conf.8*
%{_mandir}/man8/ceph-dencoder.8*
%{_mandir}/man8/ceph-diff-sorted.8*
%{_mandir}/man8/ceph-rbdnamer.8*
%{_mandir}/man8/ceph-syn.8*
%{_mandir}/man8/ceph-post-file.8*
%{_mandir}/man8/ceph.8*
%{_mandir}/man8/crushdiff.8*
%{_mandir}/man8/mount.ceph.8*
%{_mandir}/man8/rados.8*
%{_mandir}/man8/radosgw-admin.8*
%{_mandir}/man8/rbd.8*
%{_mandir}/man8/rbdmap.8*
%{_mandir}/man8/rbd-replay.8*
%{_mandir}/man8/rbd-replay-many.8*
%{_mandir}/man8/rbd-replay-prep.8*
%{_mandir}/man8/rgw-orphan-list.8*
%dir %{_datadir}/ceph/
%{_datadir}/ceph/known_hosts_drop.ceph.com
%{_datadir}/ceph/id_rsa_drop.ceph.com
%{_datadir}/ceph/id_rsa_drop.ceph.com.pub
%dir %{_sysconfdir}/ceph/
%config %{_sysconfdir}/bash_completion.d/ceph
%config %{_sysconfdir}/bash_completion.d/rados
%config %{_sysconfdir}/bash_completion.d/rbd
%config %{_sysconfdir}/bash_completion.d/radosgw-admin
%config(noreplace) %{_sysconfdir}/ceph/rbdmap
%{_unitdir}/rbdmap.service
%dir %{_udevrulesdir}
%{_udevrulesdir}/50-rbd.rules
%attr(3770,ceph,ceph) %dir %{_localstatedir}/log/ceph/
%attr(750,ceph,ceph) %dir %{_localstatedir}/lib/ceph/

%pre common
CEPH_GROUP_ID=167
CEPH_USER_ID=167
%if 0%{?rhel} || 0%{?fedora}
/usr/sbin/groupadd ceph -g $CEPH_GROUP_ID -o -r 2>/dev/null || :
/usr/sbin/useradd ceph -u $CEPH_USER_ID -o -r -g ceph -s /sbin/nologin -c "Ceph daemons" -d %{_localstatedir}/lib/ceph 2>/dev/null || :
%endif
%if 0%{?suse_version}
if ! getent group ceph >/dev/null ; then
    CEPH_GROUP_ID_OPTION=""
    getent group $CEPH_GROUP_ID >/dev/null || CEPH_GROUP_ID_OPTION="-g $CEPH_GROUP_ID"
    groupadd ceph $CEPH_GROUP_ID_OPTION -r 2>/dev/null || :
fi
if ! getent passwd ceph >/dev/null ; then
    CEPH_USER_ID_OPTION=""
    getent passwd $CEPH_USER_ID >/dev/null || CEPH_USER_ID_OPTION="-u $CEPH_USER_ID"
    useradd ceph $CEPH_USER_ID_OPTION -r -g ceph -s /sbin/nologin 2>/dev/null || :
fi
usermod -c "Ceph storage service" \
        -d %{_localstatedir}/lib/ceph \
        -g ceph \
        -s /sbin/nologin \
        ceph
%endif
exit 0

%post common
%tmpfiles_create %{_tmpfilesdir}/ceph-common.conf

%postun common
# Package removal cleanup
if [ "$1" -eq "0" ] ; then
    rm -rf %{_localstatedir}/log/ceph
    rm -rf %{_sysconfdir}/ceph
fi

%files radosgw
%{_bindir}/ceph-diff-sorted
%{_bindir}/radosgw
%{_bindir}/radosgw-token
%{_bindir}/radosgw-es
%{_bindir}/radosgw-object-expirer
%{_bindir}/rgw-gap-list
%{_bindir}/rgw-gap-list-comparator
%{_bindir}/rgw-orphan-list
%{_libdir}/libradosgw.so*
%{_mandir}/man8/radosgw.8*
%dir %{_localstatedir}/lib/ceph/radosgw
%{_unitdir}/ceph-radosgw@.service
%{_unitdir}/ceph-radosgw.target

%post radosgw
/sbin/ldconfig
%if 0%{?suse_version}
if [ $1 -eq 1 ] ; then
  /usr/bin/systemctl preset ceph-radosgw@\*.service ceph-radosgw.target >/dev/null 2>&1 || :
fi
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_post ceph-radosgw@\*.service ceph-radosgw.target
%endif
if [ $1 -eq 1 ] ; then
/usr/bin/systemctl start ceph-radosgw.target >/dev/null 2>&1 || :
fi

%preun radosgw
%if 0%{?suse_version}
%service_del_preun ceph-radosgw@\*.service ceph-radosgw.target
%endif
%if 0%{?fedora} || 0%{?rhel}
%systemd_preun ceph-radosgw@\*.service ceph-radosgw.target
%endif

%postun radosgw
/sbin/ldconfig
%systemd_postun ceph-radosgw@\*.service ceph-radosgw.target
if [ $1 -ge 1 ] ; then
  # Restart on upgrade, but only if "CEPH_AUTO_RESTART_ON_UPGRADE" is set to
  # "yes". In any case: if units are not running, do not touch them.
  SYSCONF_CEPH=%{_sysconfdir}/sysconfig/ceph
  if [ -f $SYSCONF_CEPH -a -r $SYSCONF_CEPH ] ; then
    source $SYSCONF_CEPH
  fi
  if [ "X$CEPH_AUTO_RESTART_ON_UPGRADE" = "Xyes" ] ; then
    /usr/bin/systemctl try-restart ceph-radosgw@\*.service > /dev/null 2>&1 || :
  fi
fi

%files -n librados2
%{_libdir}/librados.so.*
%dir %{_libdir}/ceph
%{_libdir}/ceph/libceph-common.so.*
%if %{with lttng}
%{_libdir}/librados_tp.so.*
%endif
%dir %{_sysconfdir}/ceph

%post -n librados2 -p /sbin/ldconfig

%postun -n librados2 -p /sbin/ldconfig

%files -n python%{python3_pkgversion}-rados
%{python3_sitearch}/rados.cpython*.so
%{python3_sitearch}/rados-*.egg-info

%if 0%{with libradosstriper}
%files -n libradosstriper1
%{_libdir}/libradosstriper.so.*

%post -n libradosstriper1 -p /sbin/ldconfig

%postun -n libradosstriper1 -p /sbin/ldconfig
%endif

%files -n librbd1
%{_libdir}/librbd.so.*
%if %{with lttng}
%{_libdir}/librbd_tp.so.*
%endif
%dir %{_libdir}/ceph/librbd
%{_libdir}/ceph/librbd/libceph_*.so*

%post -n librbd1 -p /sbin/ldconfig

%postun -n librbd1 -p /sbin/ldconfig

%files -n librgw2
%{_libdir}/librgw.so.*
%if %{with lttng}
%{_libdir}/librgw_op_tp.so.*
%{_libdir}/librgw_rados_tp.so.*
%endif

%post -n librgw2 -p /sbin/ldconfig

%postun -n librgw2 -p /sbin/ldconfig

%files -n python%{python3_pkgversion}-rgw
%{python3_sitearch}/rgw.cpython*.so
%{python3_sitearch}/rgw-*.egg-info

%files -n python%{python3_pkgversion}-rbd
%{python3_sitearch}/rbd.cpython*.so
%{python3_sitearch}/rbd-*.egg-info

%files -n libcephfs2
%{_libdir}/libcephfs.so.*
%dir %{_sysconfdir}/ceph

%post -n libcephfs2 -p /sbin/ldconfig

%postun -n libcephfs2 -p /sbin/ldconfig

%files -n python%{python3_pkgversion}-cephfs
%{python3_sitearch}/cephfs.cpython*.so
%{python3_sitearch}/cephfs-*.egg-info

%files -n python%{python3_pkgversion}-ceph-argparse
%{python3_sitelib}/ceph_argparse.py
%{python3_sitelib}/__pycache__/ceph_argparse.cpython*.py*
%{python3_sitelib}/ceph_daemon.py
%{python3_sitelib}/__pycache__/ceph_daemon.cpython*.py*

%files -n python%{python3_pkgversion}-ceph-common
%{python3_sitelib}/ceph
%{python3_sitelib}/ceph-*.egg-info

%changelog