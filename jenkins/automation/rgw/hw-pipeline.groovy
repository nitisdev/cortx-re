pipeline {
    agent {
        node {
            label "ceph-build-hw"
        }
    }
    
    triggers {
        pollSCM '*/10 * * * *'
    }

    environment {
        release_dir = "/mnt/rgw"
    }

    options {
        timeout(time: 300, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')   
        disableConcurrentBuilds()   
    }
    
    stages {

        stage('Checkout cortx-rgw') {
            steps {
                script { build_stage = env.STAGE_NAME }
                dir ('cortx-rgw') {
                checkout([$class: 'GitSCM', branches: [[name: "${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "https://github.com/Seagate/cortx-rgw"]]])
                }
            }
        }
        
        stage('Prerequisites') {
            steps {
                script { build_stage = env.STAGE_NAME }

                sh label: 'Build', script: '''                    
                pushd cortx-rgw
                    ./install-deps.sh
                    yum install rpm-build bzip2 rpmdevtools -y
                    yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/rgw-build/release/last_successful/cortx_iso/
                    echo "gpgcheck=0" >> /etc/yum.repos.d/cortx-storage.colo.seagate.com_releases_cortx_rgw-build_release_last_successful_cortx_iso_.repo
                    yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/third-party-deps/rockylinux/rockylinux-8.4-2.0.0-latest/
                    echo "gpgcheck=0" >> /etc/yum.repos.d/cortx-storage.colo.seagate.com_releases_cortx_third-party-deps_rockylinux_rockylinux-8.4-2.0.0-latest_.repo
                    yum install cortx-motr{,-devel} -y
                    
                    ./make-dist
                    rm -rf $release_dir/*
                    mkdir -p $release_dir/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
                    cp ceph*.tar.bz2 $release_dir/SOURCES/
                    
                    #tar --strip-components=1 -C $release_dir/SPECS/ --no-anchored -xvjf ceph-*tar.bz2 "ceph.spec"

                    yum install wget -y
                    wget -O $release_dir/SPECS/ceph.spec https://raw.githubusercontent.com/nitisdev/cortx-re/optimize-rgw/jenkins/automation/rgw/ceph.spec.template
                    version=$(git describe --long --match 'v*' | sed 's/^v//')
                    if expr index $version '-' > /dev/null; then
                        rpm_version=$(echo $version | cut -d - -f 1-1)
                        rpm_release=$(echo $version | cut -d - -f 2- | sed 's/-/./')
                    else
                        rpm_version=$version
                        rpm_release=0
                    fi
                    for spec in $release_dir/SPECS/ceph.spec; do
                        cat $spec |
                            sed "s/@PROJECT_VERSION@/$rpm_version/g" |
                            sed "s/@RPM_RELEASE@/$rpm_release/g" |
                            sed "s/@TARBALL_BASENAME@/ceph-$version/g" > `echo $spec | sed 's/.in$//'`
                    done

                popd
                '''
            }
        }

        stage('Build cortx-rgw packages') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Build', script: '''
                pushd $release_dir

                #time rpmbuild --clean --rmsource --define "_unpackaged_files_terminate_build 0" --define "debug_package %{nil}" --without cmake_verbose_logging --without jaeger --without lttng --without seastar --without kafka_endpoint --without zbd --without cephfs_java --without cephfs_shell --without ocf --without selinux --without ceph_test_package --without make_check --define "_binary_payload w2T16.xzdio" --define "_topdir `pwd`" -vv -ba ./SPECS/ceph.spec

                time rpmbuild --clean --rmsource --define "_unpackaged_files_terminate_build 0" --define "debug_package %{nil}" --define "_binary_payload w2T16.xzdio" --define "_topdir `pwd`" --without seastar --without cephfs_java --without ceph_test_package --without selinux --without lttng  --without cephfs_shell  --without amqp_endpoint --without kafka_endpoint --without lua_packages --without zbd --without cmake_verbose_logging --without rbd_rwl_cache --without rbd_ssd_cache  --without system_pmdk --without jaeger --without ocf --without make_check -vv -ba ./SPECS/ceph.spec

                popd    
                '''
            }
        }

    }
    post {
        always {
            cleanWs()
        }
    }
}