def getStandAloneStorageServers(){
    retry(conditions: [agent()], count: 3) {
        node(){
            configFileProvider([configFile(fileId: 'deploymentStorageConfig', variable: 'CONFIG_FILE')]) {
                def config = readJSON( file: CONFIG_FILE)
                return config['publicReleases']['urls']
            }
        }
    }
}

def getPypiConfig() {
    retry(conditions: [agent()], count: 3) {
        node(){
            configFileProvider([configFile(fileId: 'pypi_config', variable: 'CONFIG_FILE')]) {
                def config = readJSON( file: CONFIG_FILE)
                return config['deployment']['indexes']
            }
        }
    }
}

def getDefaultStandalonePath(){
    node(){
        checkout scm
        def projectMetadata = readTOML( file: 'pyproject.toml')['project']
        return "${projectMetadata.name}/${projectMetadata.version}"
    }
}

def deployStandalone(glob, url) {
    script{
        findFiles(glob: glob).each{
            try{
                def encodedUrlFileName = new URI(null, null, it.name, null).toASCIIString()
                def putResponse = httpRequest authentication: NEXUS_CREDS, httpMode: 'PUT', uploadFile: it.path, url: "${url}/${encodedUrlFileName}", wrapAsMultipart: false
                echo "http request response: ${putResponse.content}"
                echo "Deployed ${it} -> SHA256: ${sha256(it.path)}"
            } catch(Exception e){
                echo "${e}"
                throw e;
            }
        }
    }
}

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
        booleanParam(name: 'DEPLOY_PYPI', defaultValue: false, description: 'Deploy to pypi')
        booleanParam(name: 'DEPLOY_STANDALONE_PACKAGERS', defaultValue: false, description: 'Deploy standalone packages')
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
                            args '--mount source=uv_python_install_dir,target=/tmp/uvpython'
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
                                    args '--mount source=uv_python_install_dir,target=/tmp/uvpython'
                                }
                            }
                            steps{
                                sh(
                                    label: 'Package',
                                    script: '''python3 -m venv venv
                                               trap "rm -rf venv" EXIT
                                               venv/bin/pip install --disable-pip-version-check uv
                                               venv/bin/uv build
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
                            environment{
                                UV_INDEX_STRATEGY='unsafe-best-match'
                            }
                            matrix {
                                axes {
                                    axis {
                                        name 'PYTHON_VERSION'
                                        values '3.11', '3.12','3.13'
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
                                stages {
                                    stage('Test Package') {
                                        agent{
                                            label "${OS} && ${ARCHITECTURE} ${['linux', 'windows'].contains(OS) ? '&& docker': ''}"
                                        }
                                        when{
                                            expression{
                                                params.containsKey("INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()]
                                            }
                                            beforeAgent true
                                        }
                                        steps{
                                            unstash 'PYTHON_PACKAGES'
                                            script{
                                               if(['linux', 'windows'].contains(OS) && params.containsKey("INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${OS}-${ARCHITECTURE}".toUpperCase()]){
                                                   docker.image('python').inside("--mount source=uv_python_install_dir,target=${isUnix() ? '/tmp/uvpython:z': 'C:\\Users\\ContainerUser\\Documents\\uvpython'}"){
                                                        if(isUnix()){
                                                           withEnv([
                                                               'PIP_CACHE_DIR=/tmp/pipcache',
                                                               'UV_TOOL_DIR=/tmp/uvtools',
                                                               'UV_PYTHON_INSTALL_DIR=/tmp/uvpython',
                                                               'UV_CACHE_DIR=/tmp/uvcache',
                                                           ]){
                                                                sh(
                                                                   label: 'Testing with tox',
                                                                   script: """python3 -m venv venv
                                                                              ./venv/bin/pip install --disable-pip-version-check uv
                                                                              ./venv/bin/uv python install cpython-${PYTHON_VERSION}
                                                                              ./venv/bin/uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                           """
                                                               )
                                                           }
                                                        } else {
                                                           withEnv([
                                                               'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\pipcache',
                                                               'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\uvtools',
                                                               'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\uvpython',
                                                               'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\uvcache',
                                                           ]){
                                                               bat(
                                                                   label: 'Testing with tox',
                                                                   script: """python -m venv venv
                                                                              .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                              .\\venv\\Scripts\\uv python install cpython-${PYTHON_VERSION}
                                                                              .\\venv\\Scripts\\uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                                           """
                                                               )
                                                           }
                                                        }
                                                   }
                                               } else {
                                                   sh(
                                                       label: 'Testing with tox',
                                                       script: """python3 -m venv venv
                                                                  ./venv/bin/pip install --disable-pip-version-check uv
                                                                  ./venv/bin/uvx --with tox-uv tox --installpkg ${findFiles(glob: PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${PYTHON_VERSION.replace('.', '')}
                                                               """
                                                   )
                                               }
                                            }
                                        }
                                        post{
                                            cleanup{
                                                script{
                                                    if(isUnix()){
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
                    environment{
                        UV_INDEX_STRATEGY='unsafe-best-match'
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
                                sh './contrib/create_mac_distrib.sh'
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
                                sh './contrib/create_mac_distrib.sh'
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
                            environment{
                                UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\uvpython'
                            }
                            agent{
                                docker{
                                    image 'python'
                                    label 'windows && docker && x86_64'
                                    args '--mount source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\uvpython'
                                }
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                                beforeAgent true
                            }
                            steps{
                                bat(script: 'contrib/create_windows_distrib.bat')
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
        stage('Deploy'){
            when{
                anyOf{
                    equals expected: true, actual: params.DEPLOY_STANDALONE_PACKAGERS
                    equals expected: true, actual: params.DEPLOY_PYPI
                }
            }
            parallel{
                stage('Deploy to pypi') {
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
                            args '--mount source=uv_python_install_dir,target=/tmp/uvpython'
                        }
                    }
                    when{
                        allOf{
                            equals expected: true, actual: params.DEPLOY_PYPI
                            equals expected: true, actual: params.BUILD_PACKAGES
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    options{
                        retry(3)
                    }
                    input {
                        message 'Upload to pypi server?'
                        parameters {
                            choice(
                                choices: getPypiConfig(),
                                description: 'Url to the pypi index to upload python packages.',
                                name: 'SERVER_URL'
                            )
                        }
                    }
                    steps{
                        unstash 'PYTHON_PACKAGES'
                        withEnv(
                            [
                                "TWINE_REPOSITORY_URL=${SERVER_URL}",
                            ]
                        ){
                            withCredentials(
                                [
                                    usernamePassword(
                                        credentialsId: 'jenkins-nexus',
                                        passwordVariable: 'TWINE_PASSWORD',
                                        usernameVariable: 'TWINE_USERNAME'
                                    )
                                ]
                            ){
                                sh(
                                    label: 'Uploading to pypi',
                                    script: '''python3 -m venv venv
                                               trap "rm -rf venv" EXIT
                                               . ./venv/bin/activate
                                               pip install --disable-pip-version-check uv
                                               uvx --with-requirements=requirements-dev.txt twine upload --disable-progress-bar --non-interactive dist/*
                                            '''
                                )
                            }
                        }
                    }
                    post{
                        cleanup{
                            cleanWs(
                                deleteDirs: true,
                                patterns: [
                                        [pattern: 'dist/', type: 'INCLUDE']
                                    ]
                            )
                        }
                    }
                }
                stage('Deploy Standalone'){
                    when {
                        allOf{
                            expression{return standaloneVersions.size() > 0}
                            equals expected: true, actual: params.DEPLOY_STANDALONE_PACKAGERS
                            anyOf{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                                equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                            }
                        }
                        beforeAgent true
                        beforeInput true
                    }
                    input {
                        message 'Upload to Nexus server?'
                        parameters {
                            credentials credentialType: 'com.cloudbees.plugins.credentials.common.StandardCredentials', defaultValue: 'jenkins-nexus', name: 'NEXUS_CREDS', required: true
                            choice(
                                choices: getStandAloneStorageServers(),
                                description: 'Url to upload artifact.',
                                name: 'SERVER_URL'
                            )
                            string defaultValue: getDefaultStandalonePath(), description: 'subdirectory to store artifact', name: 'archiveFolder'
                        }
                    }
                    stages{
                        stage('Deploy Standalone Applications'){
                            agent any
                            steps{
                                script{
                                    standaloneVersions.each{
                                        unstash "${it}"
                                    }
                                    deployStandalone('dist/*.zip', "${SERVER_URL}/${archiveFolder}")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}