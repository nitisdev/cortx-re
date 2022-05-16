pipeline {
    agent {
        node {
            label 'ceph-build-hw'
        }
    }

    options {
        timeout(time: 240, unit: 'MINUTES')
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30', numToKeepStr: '30'))
        ansiColor('xterm')
        disableConcurrentBuilds()   
    }

    parameters {
        string(name: 'CORTX_RE_REPO', defaultValue: 'https://github.com/Seagate/cortx-re/', description: 'Repository for Cluster Setup scripts', trim: true)
        string(name: 'CORTX_RE_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for Cluster Setup scripts', trim: true)
        string(name: 'CORTX_RGW_REPO', defaultValue: 'https://github.com/Seagate/cortx-rgw/', description: 'Repository for Cluster Setup scripts', trim: true)
        string(name: 'CORTX_RGW_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for Cluster Setup scripts', trim: true)
        choice(
            name: 'BUILD_OS',
            choices: ['Ubuntu', 'CentOS', 'Rocky Linux'],
            description: 'OS to build binary packages for (*.deb, *.rpm).'
        )
    }    

    stages {
        stage('Checkout Script') {
            steps { 
                cleanWs()            
                script {
                    checkout([$class: 'GitSCM', branches: [[name: "${CORTX_RE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CORTX_RE_REPO}"]]])                
                }
            }
        }

        stage ('Build CORTX-RGW Binary Packages') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Build Binary Packages', script: '''
                    pushd solutions/kubernetes/
                        export CORTX_RGW_REPO=${CORTX_RGW_REPO}
                        export CORTX_RGW_BRANCH=${CORTX_RGW_BRANCH}
                        export BUILD_OS=${BUILD_OS}
                        bash cortx-rgw-binary-build.sh --cortx-rgw-build-env /var/log/cortx-rgw-build
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