#!/bin/bash
#
# Copyright (c) 2022 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

######################################################################
# This script is specific for the reserved HW by RE team.
# To use on other HW/VM please install docker and change
# container volume $MOUNT_LOCATION for build os container.
######################################################################

source functions.sh

BUILD_LOCATION="$2"

function usage() {
    cat << HEREDOC
Usage : $0 [--cortx-rgw-build] [BUILD_LOCATION]
where,
    --cortx-rgw-build - Build cortx-rgw binary packages.
    --cortx-rgw-build-env - Build cortx-rgw binary packages inside container environment.
    BUILD_LOCATION - Build location on disk.
HEREDOC
}

ACTION="$1"
if [ -z "$ACTION" ]; then
    echo "ERROR : No option provided"
    usage
    exit 1
fi

function check_params() {
    add_primary_separator "Checking parameters"
    if [ -z "$CORTX_RGW_REPO" ]; then echo "CORTX_RGW_REPO not provided. Using default: Seagate/cortx-rgw ";CORTX_RGW_REPO="Seagate/cortx-rgw"; fi
    if [ -z "$CORTX_RGW_BRANCH" ]; then echo "CORTX_RGW_BRANCH not provided. Using default: quincy";CORTX_RGW_BRANCH="main"; fi
    if [ -z "$BUILD_OS" ]; then echo "BUILD_OS not provided. Using default: centos";BUILD_OS="centos"; fi
    if [ -z "$BUILD_LOCATION" ]; then echo "BUILD_LOCATION for container to mount not provided. Using default: /var/log/cortx-rgw-build";BUILD_LOCATION="/var/log/cortx-rgw-build"; fi

   echo -e "\n\n########################################################################"
   echo -e "# CORTX_RGW_REPO         : $CORTX_RGW_REPO          "
   echo -e "# CORTX_RGW_BRANCH       : $CORTX_RGW_BRANCH        "
   echo -e "# BUILD_OS               : $BUILD_OS                "
   echo -e "# BUILD_LOCATION         : $BUILD_LOCATION          "
   echo -e "#########################################################################"
}

function prereq() {
    add_primary_separator "\t\tRunning Preequisites"

    mkdir -p "$BUILD_LOCATION"

    pushd "$BUILD_LOCATION"
        add_common_separator "Removing previous files"
        rm -rvf *
    popd

    if [[ "$ACTION" == "--cortx-rgw-build-env" ]]; then
        add_secondary_separator "Copy build scripts to $BUILD_LOCATION/$BUILD_OS"
        mkdir -p "$BUILD_LOCATION/$BUILD_OS"
        cp $0 "$BUILD_LOCATION/$BUILD_OS/build.sh"
        cp functions.sh "$BUILD_LOCATION/$BUILD_OS"
    fi
}

function prvsn_env() {
    add_primary_separator "\tProvision $BUILD_OS Build Environment"

    add_secondary_separator "Verify docker installation"
    if ! which docker; then
        add_common_separator "Installing Docker on Build Node Agent"
        curl -fsSL https://get.docker.com -o get-docker.sh
        chmod +x get-docker.sh
        ./get-docker.sh
    fi

    if [[ "$BUILD_OS" == "Ubuntu" ]]; then
        if [[ $(docker images --format "{{.Repository}}:{{.Tag}}" --filter reference=ubuntu:20.04) != "ubuntu:20.04" ]]; then
            docker pull ubuntu:20.04
        fi
        add_secondary_separator "Run Ubuntu 20.04 container and run build script"
        docker run --rm -t -e CORTX_RGW_REPO=$CORTX_RGW_REPO -e CORTX_RGW_BRANCH=$CORTX_RGW_BRANCH -e BUILD_LOCATION="/home" --name cortx_rgw_ubuntu -v "$BUILD_LOCATION/$BUILD_OS":/home --entrypoint /bin/bash ubuntu:20.04 -c "pushd /home && ./build.sh --env-build && popd"

    elif [[ "$BUILD_OS" == "CentOS" ]]; then
        if [[ $(docker images --format "{{.Repository}}:{{.Tag}}" --filter reference=centos:8) != "centos:8" ]]; then
            docker pull centos:8
        fi
        add_secondary_separator "Run CentOS 8 container and run build script"
        docker run --rm -t -e CORTX_RGW_REPO=$CORTX_RGW_REPO -e CORTX_RGW_BRANCH=$CORTX_RGW_BRANCH  -e BUILD_LOCATION="/home" --name cortx_rgw_centos -v "$BUILD_LOCATION/$BUILD_OS":/home --entrypoint /bin/bash centos:8 -c "pushd /home && ./build.sh --env-build && popd"

    elif [[ "$BUILD_OS" == "Rocky Linux" ]]; then
        if [[ $(docker images --format "{{.Repository}}:{{.Tag}}" --filter reference=rockylinux:8) != "rockylinux:8" ]]; then
            docker pull rockylinux:8
        fi
        add_secondary_separator "Run Rocky Linux 8 container and run build script"
        docker run --rm -t -e CORTX_RGW_REPO=$CORTX_RGW_REPO -e CORTX_RGW_BRANCH=$CORTX_RGW_BRANCH  -e BUILD_LOCATION="/home" --name cortx_rgw_rockylinux -v "$BUILD_LOCATION/$BUILD_OS":/home --entrypoint /bin/bash rockylinux:8 -c "pushd /home && ./build.sh --env-build && popd"

    else
        add_secondary_separator "Failed to build cortx-rgw, please check logs"
    fi
}

function cortx_rgw_build() {
    add_primary_separator "\t\tStart CORTX-RGW Build"

    source /etc/os-release
    case "$ID" in
        ubuntu)
            add_primary_separator "Building Ubuntu cortx-rgw binary packages"
            add_common_separator "Update repolist cache and install prerequisites"
            apt update && apt install git -y
            DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata
            pushd "$BUILD_LOCATION"
                add_common_separator "Clone Repo"
                git clone $CORTX_RGW_REPO -b $CORTX_RGW_BRANCH

                pushd cortx-rgw
                    add_common_separator "Checkout Submodules"
                    git submodule update --init --recursive

                    add_common_separator "Install Dependencies"
                    ./install-deps.sh

                    add_common_separator "Make Source Tarball"
                    ./make-dist
                    
                    mv ceph-*tar.bz2 ../
                    version=$(git describe --long --match 'v*' | sed 's/^v//')
                popd

                tar -xf ceph-*tar.bz2
                pushd ceph-"$version"
                    add_common_separator "Start Build"
                    dpkg-buildpackage -us -uc
                popd

                add_common_separator "List generated binary packages (*.deb)"
                ls *.deb
            popd
        ;;
        centos)
                add_primary_separator "Building centos binary packages"
                add_common_separator "Update repolist cache and install prerequisites"
                rpm -ivh http://mirror.centos.org/centos/8-stream/BaseOS/x86_64/os/Packages/centos-gpg-keys-8-3.el8.noarch.rpm
                dnf --disablerepo '*' --enablerepo=extras swap centos-linux-repos centos-stream-repos -y
                yum makecache && yum install git -y
                yum install wget bzip2 yum-utils epel-release rpm-build rpmdevtools dnf-plugins-core -y
                dnf config-manager --set-enabled powertools
                yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/rgw-build/release/last_successful/cortx_iso/
                echo "gpgcheck=0" >> /etc/yum.repos.d/cortx-storage.colo.seagate.com_releases_cortx_rgw-build_release_last_successful_cortx_iso_.repo
                yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/third-party-deps/rockylinux/rockylinux-8.4-2.0.0-latest/
                echo "gpgcheck=0" >> /etc/yum.repos.d/cortx-storage.colo.seagate.com_releases_cortx_third-party-deps_rockylinux_rockylinux-8.4-2.0.0-latest_.repo
                yum install cortx-motr{,-devel} -y
                pushd "$BUILD_LOCATION"
                    add_common_separator "Clone Repo"
                    git clone $CORTX_RGW_REPO -b $CORTX_RGW_BRANCH

                    pushd cortx-rgw
                        add_common_separator "Checkout Submodules"
                        git submodule update --init --recursive

                        add_common_separator "Install Dependencies"
                        ./install-deps.sh

                        add_common_separator "Make Source Tarball"
                        ./make-dist
                        
                        mkdir -p ../rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
                        tar --strip-components=1 -C ../rpmbuild/SPECS --no-anchored -xvjf ceph-*tar.bz2 "ceph.spec"
                        mv ceph*tar.bz2 ../rpmbuild/SOURCES/
                    popd

                    pushd rpmbuild
                        add_common_separator "Start Build"
                        rpmbuild --define "_topdir `pwd`" -ba SPECS/ceph.spec
                    popd

                    add_common_separator "List generated binary packages (*.rpm)"
                    ls rpmbuild/RPMS/*
                popd
        ;;
        rocky)
                add_primary_separator "Building rocky linux binary packages"
                add_common_separator "Update repolist cache and install prerequisites"
                yum makecache && yum install git -y
                yum install wget bzip2 yum-utils epel-release rpm-build rpmdevtools dnf-plugins-core -y
                dnf config-manager --set-enabled powertools
                yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/rgw-build/release/last_successful/cortx_iso/
                echo "gpgcheck=0" >> /etc/yum.repos.d/cortx-storage.colo.seagate.com_releases_cortx_rgw-build_release_last_successful_cortx_iso_.repo
                yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/third-party-deps/rockylinux/rockylinux-8.4-2.0.0-latest/
                echo "gpgcheck=0" >> /etc/yum.repos.d/cortx-storage.colo.seagate.com_releases_cortx_third-party-deps_rockylinux_rockylinux-8.4-2.0.0-latest_.repo
                yum install cortx-motr{,-devel} -y
                pushd "$BUILD_LOCATION"
                    add_common_separator "Clone Repo"
                    git clone $CORTX_RGW_REPO -b $CORTX_RGW_BRANCH

                    pushd cortx-rgw
                        add_common_separator "Checkout Submodules"
                        git submodule update --init --recursive

                        add_common_separator "Install Dependencies"
                        ./install-deps.sh

                        add_common_separator "Make Source Tarball"
                        ./make-dist
                        
                        mkdir -p ../rpmbuild/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
                        tar --strip-components=1 -C ../rpmbuild/SPECS --no-anchored -xvjf ceph-*tar.bz2 "ceph.spec"
                        mv ceph*tar.bz2 ../rpmbuild/SOURCES/
                    popd

                    pushd rpmbuild
                        add_common_separator "Start Build"
                        rpmbuild --define "_topdir `pwd`" -ba SPECS/ceph.spec
                    popd

                    add_common_separator "List generated binary packages (*.rpm)"
                    ls rpmbuild/RPMS/*
                popd
        ;;
    esac
}

case $ACTION in
    --cortx-rgw-build)
        check_params
        prereq
        cortx_rgw_build
    ;;
    --cortx-rgw-build-env)
        check_params
        prereq
        prvsn_env
    ;;
    --env-build)
        cortx_rgw_build
    ;;
    *)
        echo "ERROR : Please provide a valid option"
        usage
        exit 1
    ;;
esac