standaloneVersions = []

pipeline {
    agent none
    parameters{
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'PACKAGE_STANDALONE_WINDOWS_INSTALLER', defaultValue: false, description: 'Create a standalone Windows version that does not require a user to install python first')
        booleanParam(name: 'PACKAGE_MAC_OS_STANDALONE_X86_64', defaultValue: false, description: 'Create a standalone version for MacOS X86_64 (m1) machines')
        booleanParam(name: 'PACKAGE_MAC_OS_STANDALONE_ARM64', defaultValue: false, description: 'Create a standalone version for MacOS ARM64 (Intel) machines')
    }
    stages {
        stage('Building and Resting'){
            stages{
                stage('Build and Test'){
                    environment{
                        PIP_CACHE_DIR='/tmp/pipcache'
                        UV_INDEX_STRATEGY='unsafe-best-match'
                        UV_TOOL_DIR='/tmp/uvtools'
                        UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                        UV_CACHE_DIR='/tmp/uvcache'
                    }
                    agent {
                        docker{
                            image 'python'
                            label 'docker && linux'
                            args "--mount source=uv_python_install_dir,target=/tmp/uvpython"
                        }

                    }
                    stages{
                        stage('Setup CI Environment'){
                            steps{
                                sh(
                                    label: 'Create virtual environment with packaging in development mode',
                                    script: '''python3 -m venv --clear bootstrap_uv
                                               trap "rm -rf bootstrap_uv" EXIT
                                               bootstrap_uv/bin/pip install --disable-pip-version-check uv
                                               rm -rf venv
                                               bootstrap_uv/bin/uv venv venv
                                               . ./venv/bin/activate
                                               bootstrap_uv/bin/uv pip install uv
                                               rm -rf bootstrap_uv
                                               uv pip install -r requirements-dev.txt -e .
                                               '''
                               )
                            }
                        }
                        stage('Run Tests'){
                            when{
                                equals expected: true, actual: params.RUN_CHECKS
                                beforeAgent true
                            }
                            parallel {
                                stage('Run PyTest Unit Tests'){
                                    steps{
                                        catchError(buildResult: 'UNSTABLE', message: 'Did not pass all pytest tests', stageResult: 'UNSTABLE') {
                                            sh(
                                                script: '''. ./venv/bin/activate
                                                           PYTHONFAULTHANDLER=1 coverage run --parallel-mode --source=avtool -m pytest --junitxml=./reports/tests/pytest/pytest-junit.xml --capture=no
                                                       '''
                                            )
                                        }
                                    }
                                    post {
                                        always {
                                            junit(allowEmptyResults: true, testResults: 'reports/tests/pytest/pytest-junit.xml')
                                        }
                                    }
                                }
                                stage('Task Scanner'){
                                    steps{
                                        recordIssues(tools: [taskScanner(highTags: 'FIXME', includePattern: 'speedwagon/**/*.py', normalTags: 'TODO')])
                                    }
                                }
                            }
                            post{
                                always{
                                    sh '''. ./venv/bin/activate
                                          coverage combine && coverage xml -o reports/coverage.xml && coverage html -d reports/coverage
                                       '''
                                    recordCoverage(tools: [[parser: 'COBERTURA', pattern: 'reports/coverage.xml']])
                                }
                            }
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                    [pattern: '.pytest_cache/', type: 'INCLUDE'],
                                    [pattern: '*.egg-info', type: 'INCLUDE'],
                                    [pattern: 'coverage/', type: 'INCLUDE'],
                                    [pattern: '**/.coverage', type: 'INCLUDE'],
                                    [pattern: 'venv/', type: 'INCLUDE'],
                                    [pattern: 'logs/', type: 'INCLUDE'],
                                    [pattern: 'reports/', type: 'INCLUDE'],
                                    [pattern: 'coverage-sources.zip', type: 'INCLUDE'],
                                    [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                ]
                            )
                        }
                    }
                }
            }
        }
        stage('Package'){
            stages{
                stage('Standalone'){
                    when{
                        anyOf{
                            equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                            equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                            equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                        }
                    }
                    parallel{
                        stage('Mac Application Bundle x86_64'){
                            agent{
                                label 'mac && python3.12 && x86_64'
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                                beforeAgent true
                            }
                            steps{
                                sh 'UV_INDEX_STRATEGY=unsafe-best-match ./contrib/create_mac_distrib.sh'
                            }
                            post{
                                success{
                                    archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                    stash includes: 'dist/*.zip', name: 'APPLE_APPLICATION_X86_64'
                                    script{
                                        standaloneVersions << 'APPLE_APPLICATION_X86_64'
                                    }
                                }
                                cleanup{
                                    sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                    cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: 'build/', type: 'INCLUDE'],
                                            [pattern: 'dist/', type: 'INCLUDE'],
                                            [pattern: '*.egg-info/', type: 'INCLUDE'],
                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                       ]
                                    )
                                }
                            }
                        }
                        stage('Mac Application Bundle arm64'){
                            agent{
                                label 'mac && python3.12 && arm64'
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                                beforeAgent true
                            }
                            steps{
                                sh 'UV_INDEX_STRATEGY=unsafe-best-match ./contrib/create_mac_distrib.sh'
                            }
                            post{
                                success{
                                    archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                    stash includes: 'dist/*.zip', name: 'APPLE_APPLICATION_ARM64'
                                    script{
                                        standaloneVersions << 'APPLE_APPLICATION_ARM64'
                                    }
                                }
                                cleanup{
                                    sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                    cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: 'build/', type: 'INCLUDE'],
                                            [pattern: 'dist/', type: 'INCLUDE'],
                                            [pattern: '*.egg-info/', type: 'INCLUDE'],
                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                        ]
                                    )
                                }
                            }
                        }
                        stage('Windows Application'){
                            agent{
                                docker{
                                    image 'python'
                                    label 'windows && docker && x86_64'
                                }
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                                beforeAgent true
                            }
                            steps{
                                bat(script: '''set UV_INDEX_STRATEGY=unsafe-best-match
                                               contrib/create_windows_distrib.bat
                                               '''
                               )
                            }
                            post{
                                success{
                                    archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                    stash includes: 'dist/*.zip', name: 'WINDOWS_APPLICATION_X86_64'
                                    script{
                                        standaloneVersions << 'WINDOWS_APPLICATION_X86_64'
                                    }
                                }
                                cleanup{
                                    cleanWs(
                                        deleteDirs: true,
                                        patterns: [
                                            [pattern: 'build/', type: 'INCLUDE'],
                                            [pattern: 'dist/', type: 'INCLUDE'],
                                            [pattern: '*.egg-info/', type: 'INCLUDE'],
                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                        ]
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}