def call(){
    def standaloneVersions = []
    pipeline {
        agent none
        parameters{
            booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
            booleanParam(name: 'BUILD_PACKAGES', defaultValue: false, description: 'Build Python packages')
            booleanParam(name: 'TEST_PACKAGES', defaultValue: false, description: 'Test packages')
            booleanParam(name: 'INCLUDE_LINUX-X86_64', defaultValue: true, description: 'Include x86_64 architecture for Linux')
            booleanParam(name: 'INCLUDE_LINUX-ARM64', defaultValue: false, description: 'Include ARM architecture for Linux')
            booleanParam(name: 'INCLUDE_MACOS-X86_64', defaultValue: false, description: 'Include x86_64 architecture for Mac')
            booleanParam(name: 'INCLUDE_MACOS-ARM64', defaultValue: false, description: 'Include ARM(m1) architecture for Mac')
            booleanParam(name: 'INCLUDE_WINDOWS-X86_64', defaultValue: false, description: 'Include x86_64 architecture for Windows')
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
                    stage('Python Packages'){
                        when{
                            equals expected: true, actual: params.BUILD_PACKAGES
                        }
                        stages{
                            stage('Create Python Packages'){
                                environment{
                                    PIP_CACHE_DIR='/tmp/pipcache'
                                    UV_INDEX_STRATEGY='unsafe-best-match'
                                    UV_CACHE_DIR='/tmp/uvcache'
                                }
                                agent {
                                    docker {
                                        image 'python'
                                        label 'docker && linux'
                                        args '--mount source=python-tmp-galatea,target=/tmp'
                                    }
                                }
                                steps{
                                    sh(
                                        label: 'Package',
                                        script: '''python3 -m venv venv && venv/bin/pip install --disable-pip-version-check uv
                                                   . ./venv/bin/activate
                                                   uv build
                                                '''
                                    )
                                }
                                post{
                                    always{
                                        archiveArtifacts artifacts: 'dist/*.whl,dist/*.tar.gz,dist/*.zip', fingerprint: true
                                        stash includes: 'dist/*.whl,dist/*.tar.gz,dist/*.zip', name: 'PYTHON_PACKAGES'
                                    }
                                    cleanup{
                                        cleanWs(patterns: [
                                                [pattern: 'venv/', type: 'INCLUDE'],
                                                [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                        ])
                                    }
                                }
                            }
                            stage('Testing packages'){
                                when{
                                    equals expected: true, actual: params.TEST_PACKAGES
                                }
                                matrix {
                                    axes {
                                        axis {
                                            name 'PYTHON_VERSION'
                                            values '3.12','3.13'
                                        }
                                        axis {
                                            name 'OS'
                                            values 'linux','macos','windows'
                                        }
                                        axis {
                                            name 'ARCHITECTURE'
                                            values 'x86_64', 'arm64'
                                        }
                                        axis {
                                            name 'PACKAGE_TYPE'
                                            values 'wheel', 'sdist'
                                        }
                                    }
                                    excludes {
                                        exclude {
                                            axis {
                                                name 'OS'
                                                values 'windows'
                                            }
                                            axis {
                                                name 'ARCHITECTURE'
                                                values 'arm64'
                                            }
                                        }
                                    }
                                    when{
                                        equals expected: true, actual: params.TEST_PACKAGES
                                    }
                                    stages {
                                        stage('Test Package in container') {
                                            environment{
                                                PIP_CACHE_DIR="${isUnix() ? '/tmp/pipcache': 'C:\\Users\\ContainerUser\\Documents\\pipcache'}"
                                                UV_INDEX_STRATEGY='unsafe-best-match'
                                                UV_TOOL_DIR="${isUnix() ? '/tmp/uvtools': 'C:\\Users\\ContainerUser\\Documents\\uvtools'}"
                                                UV_PYTHON_INSTALL_DIR="${isUnix() ? '/tmp/uvpython': 'C:\\Users\\ContainerUser\\Documents\\uvpython'}"
                                                UV_CACHE_DIR="${isUnix() ? '/tmp/uvcache': 'C:\\Users\\ContainerUser\\Documents\\uvcache'}"
                                            }
                                            when{
                                                expression{
                                                    ['linux', 'windows'].contains(OS) && params.containsKey("INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()]
                                                }
                                                beforeAgent true
                                            }
                                            agent {
                                                docker {
                                                    image 'python'
                                                    label "${OS} && ${ARCHITECTURE} && docker"
                                                }
                                            }
                                            steps {
                                                unstash 'PYTHON_PACKAGES'
                                                script{
                                                    if(isUnix()){
                                                        sh(
                                                            label: 'Testing with tox',
                                                            script: """python3 -m venv venv
                                                                       venv/bin/pip install --disable-pip-version-check uv
                                                                       venv/bin/uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                    """
                                                        )
                                                    } else {
                                                        bat(
                                                            label: 'Testing with tox',
                                                            script: """python -m venv venv
                                                                       .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                       .\\venv\\Scripts\\uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                    """
                                                        )
                                                    }
                                                }
                                            }
                                            post{
                                                cleanup{
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
                                                            [pattern: '**/__pycache__/', type: 'INCLUDE'],
                                                            ]
                                                    )
                                                }
                                            }
                                        }
                                        stage('Test Package directly on agent') {
                                            when{
                                                expression{['macos'].contains(OS) && params["INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()]}
                                                beforeAgent true
                                            }
                                            agent {
                                                label "${OS} && ${ARCHITECTURE}"
                                            }
                                            steps {
                                                script{
                                                        unstash 'PYTHON_PACKAGES'
                                                        sh(
                                                            label: 'Testing with tox',
                                                            script: """python3 -m venv venv
                                                                       . ./venv/bin/activate
                                                                       pip install uv
                                                                       UV_INDEX_STRATEGY=unsafe-best-match uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                    """
                                                        )
                                                }
                                            }
                                            post{
                                                cleanup{
                                                    script{
                                                        if (isUnix()){
                                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        } else {
                                                            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        }
                                                    }
                                                    cleanWs(
                                                        patterns: [
                                                            [pattern: 'dist/', type: 'INCLUDE'],
                                                            [pattern: 'venv/', type: 'INCLUDE'],
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
}