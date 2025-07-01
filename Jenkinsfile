import org.jenkinsci.plugins.pipeline.modeldefinition.Utils
library identifier: 'JenkinsPythonHelperLibrary@2024.12.0', retriever: modernSCM(
  [$class: 'GitSCMSource',
   remote: 'https://github.com/UIUCLibrary/JenkinsPythonHelperLibrary.git',
   ])

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
def get_sonarqube_unresolved_issues(report_task_file){
    script{

        def props = readProperties  file: report_task_file
        def response = httpRequest url : props['serverUrl'] + '/api/issues/search?componentKeys=' + props['projectKey'] + '&resolved=no'
        def outstandingIssues = readJSON text: response.content
        return outstandingIssues
    }
}

def deploySingleStandalone(file, url, authentication) {
    script{
        try{
            def encodedUrlFileName = new URI(null, null, file.name, null).toASCIIString()
            def newUrl = "${url}/${encodedUrlFileName}"
            def putResponse = httpRequest authentication: authentication, httpMode: 'PUT', uploadFile: file.path, url: "${newUrl}", wrapAsMultipart: false
            return newUrl
        } catch(Exception e){
            echo "${e}"
            throw e;
        }
    }
}

def createChocolateyConfigFile(configJsonFile, installerPackage, url){
    def deployJsonMetadata = [
        "PackageVersion": readTOML( file: 'pyproject.toml')['project'].version,
        "DownloadUrl": url,
        "PackageFile": installerPackage.name,
        "Sha256": sha256(installerPackage.path),
        "TabCompletionPowershellModule": "${installerPackage.name.take(installerPackage.name.lastIndexOf('.'))}\\extras\\cli_completion\\powershell\\tripwire.complete.psm1"

    ]
    writeJSON( json: deployJsonMetadata, file: configJsonFile, pretty: 2)
}


pipeline {
    agent none
    parameters{
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
        booleanParam(name: 'USE_SONARQUBE', defaultValue: true, description: 'Send data test data to SonarQube')
        credentials(name: 'SONARCLOUD_TOKEN', credentialType: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl', defaultValue: 'sonarcloud_token', required: false)
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
        stage('Building and Testing'){
            stages{
                stage('Build and Test'){
                    environment{
                        PIP_CACHE_DIR='/tmp/pipcache'
                        UV_INDEX_STRATEGY='unsafe-best-match'
                        UV_TOOL_DIR='/tmp/uvtools'
                        UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                        UV_CACHE_DIR='/tmp/uvcache'
                        UV_CONSTRAINT='requirements-dev.txt'
                    }
                    agent {
                        docker{
                            image 'python'
                            label 'docker && linux && x86_64'
                            args '--mount source=tripwire_cache,target=/tmp'
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
                        stage('Build Documentation'){
                            steps{
                                catchError(buildResult: 'UNSTABLE', message: 'Sphinx has warnings', stageResult: 'UNSTABLE') {
                                    sh '''. ./venv/bin/activate
                                          python -m sphinx --builder=html -W --keep-going -w logs/build_sphinx_html.log -d build/docs/.doctrees docs dist/docs/html
                                       '''
                               }
                            }
                            post{
                                success{
                                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'dist/docs/html', reportFiles: 'index.html', reportName: 'Documentation', reportTitles: ''])
                                    script{
                                        def props = readTOML( file: 'pyproject.toml')['project']
                                        zip archive: true, dir: 'dist/docs/html', glob: '', zipFile: "dist/${props.name}-${props.version}.doc.zip"
                                    }
                                }
                                always{
                                    recordIssues(tools: [sphinxBuild(pattern: 'logs/build_sphinx_html.log')])
                                }
                            }
                        }
                        stage('Run Tests'){
                            when{
                                equals expected: true, actual: params.RUN_CHECKS
                                beforeAgent true
                            }
                            parallel {
                                stage('PyTest'){
                                    steps{
                                        catchError(buildResult: 'UNSTABLE', message: 'Did not pass all pytest tests', stageResult: 'UNSTABLE') {
                                            sh(
                                                script: '''. ./venv/bin/activate
                                                           PYTHONFAULTHANDLER=1 coverage run --parallel-mode --source=uiucprescon.tripwire -m pytest --junitxml=./reports/tests/pytest/pytest-junit.xml --capture=no
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
                                stage('Documentation Doctest'){
                                    steps {
                                        sh(
                                            label: 'Running Doctest Tests',
                                            script: '''. ./venv/bin/activate
                                                       coverage run --parallel-mode --source=uiucprescon/tripwire -m sphinx -b doctest docs/ dist/docs/html -d build/docs/doctrees --no-color -w logs/doctest.txt
                                                    '''
                                            )
                                    }
                                    post{
                                        always {
                                            recordIssues(tools: [sphinxBuild(id: 'doctest', name: 'Doctest', pattern: 'logs/doctest.txt')])
                                        }
                                    }
                                }
                                stage('Documentation Doctest - linkcheck'){
                                    steps {
                                        catchError(buildResult: 'SUCCESS', message: 'Sphinx docs linkcheck', stageResult: 'UNSTABLE') {
                                            sh(
                                                label: 'Running Sphinx docs linkcheck',
                                                script: '''. ./venv/bin/activate
                                                           python -m sphinx -b doctest docs/ build/docs -d build/docs/doctrees --no-color --builder=linkcheck --fail-on-warning
                                                           '''
                                                )
                                        }
                                    }
                                }
                                stage('Task Scanner'){
                                    steps{
                                        recordIssues(tools: [taskScanner(highTags: 'FIXME', includePattern: 'tripwire/**/*.py', normalTags: 'TODO')])
                                    }
                                }
                                stage('Ruff') {
                                    steps{
                                        catchError(buildResult: 'SUCCESS', message: 'Ruff found issues', stageResult: 'UNSTABLE') {
                                            sh(
                                             label: 'Running Ruff',
                                             script: '''. ./venv/bin/activate
                                                        ruff check --config=pyproject.toml -o reports/ruffoutput.txt --output-format pylint --exit-zero
                                                        ruff check --config=pyproject.toml -o reports/ruffoutput.json --output-format json
                                                    '''
                                             )
                                        }
                                    }
                                    post{
                                        always{
                                            recordIssues(tools: [pyLint(pattern: 'reports/ruffoutput.txt', name: 'Ruff')])
                                        }
                                    }
                                }
                                stage('MyPy'){
                                    steps{
                                        catchError(buildResult: 'SUCCESS', message: 'MyPy found issues', stageResult: 'UNSTABLE') {
                                            tee('logs/mypy.log'){
                                                sh(label: 'Running MyPy',
                                                   script: '. ./venv/bin/activate && mypy -p uiucprescon.tripwire --html-report reports/mypy/html'
                                                )
                                            }
                                        }
                                    }
                                    post {
                                        always {
                                            recordIssues(tools: [myPy(pattern: 'logs/mypy.log')])
                                            publishHTML([allowMissing: true, alwaysLinkToLastBuild: false, keepAll: false, reportDir: 'reports/mypy/html/', reportFiles: 'index.html', reportName: 'MyPy HTML Report', reportTitles: ''])
                                        }
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
                        stage('Submit results to SonarQube'){
                            options{
                                lock('tripwire-sonarscanner')
                            }
                            environment{
                                VERSION="${readTOML( file: 'pyproject.toml')['project'].version}"
                            }
                            when{
                                allOf{
                                    equals expected: true, actual: params.USE_SONARQUBE
                                    expression{
                                        try{
                                            withCredentials([string(credentialsId: params.SONARCLOUD_TOKEN, variable: '$$$$$$$')]) {
                                                echo 'Found credentials for sonarqube'
                                            }
                                        } catch(e){
                                            return false
                                        }
                                        return true
                                    }
                                }
                            }
                            steps{
                                withSonarQubeEnv(installationName: 'sonarcloud', credentialsId: params.SONARCLOUD_TOKEN) {
                                    sh(
                                        label: 'Running Sonar Scanner',
                                        script: "./venv/bin/uvx pysonar-scanner -Dsonar.projectVersion=${env.VERSION} -Dsonar.python.xunit.reportPath=./reports/tests/pytest/pytest-junit.xml -Dsonar.python.coverage.reportPaths=./reports/coverage.xml -Dsonar.python.ruff.reportPaths=./reports/ruffoutput.json -Dsonar.python.mypy.reportPaths=./logs/mypy.log ${env.CHANGE_ID ? '-Dsonar.pullrequest.key=$CHANGE_ID -Dsonar.pullrequest.base=$BRANCH_NAME' : '-Dsonar.branch.name=$BRANCH_NAME' }",
                                    )
                                }
                                script{
                                    timeout(time: 1, unit: 'HOURS') {
                                        def sonarqubeResult = waitForQualityGate(abortPipeline: false, credentialsId: params.SONARCLOUD_TOKEN)
                                        if (sonarqubeResult.status != 'OK') {
                                           unstable "SonarQube quality gate: ${sonarqubeResult.status}"
                                       }
                                       if(env.BRANCH_IS_PRIMARY){
                                           def outstandingIssues = get_sonarqube_unresolved_issues('.scannerwork/report-task.txt')
                                           writeJSON file: 'reports/sonar-report.json', json: outstandingIssues
                                           recordIssues(tools: [sonarQube(pattern: 'reports/sonar-report.json')])
                                       }
                                    }
                                }
                            }
                            post{
                                always{
                                    milestone ordinal: 1, label: 'sonarcloud'
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
                                UV_TOOL_DIR='/tmp/uvtools'
                                UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                                UV_CONSTRAINT='requirements-dev.txt'
                            }
                            agent {
                                docker {
                                    image 'python'
                                    label 'docker && linux'
                                    args '--mount source=tripwire_cache,target=/tmp'
                                }
                            }
                            steps{
                                sh(
                                    label: 'Package',
                                    script: '''python3 -m venv venv
                                               trap "rm -rf venv" EXIT
                                               venv/bin/pip install --disable-pip-version-check uv
                                               venv/bin/uv build --build-constraints=requirements-dev.txt
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
                                UV_CONSTRAINT='requirements-dev.txt'
                            }
                            steps{
                                customMatrix(
                                    axes: [
                                        [
                                            name: 'PYTHON_VERSION',
                                            values: ['3.11', '3.12','3.13']
                                        ],
                                        [
                                            name: 'OS',
                                            values: ['linux','macos','windows']
                                        ],
                                        [
                                            name: 'ARCHITECTURE',
                                            values: ['x86_64', 'arm64']
                                        ],
                                        [
                                            name: 'PACKAGE_TYPE',
                                            values: ['wheel', 'sdist'],
                                        ]
                                    ],
                                    excludes: [
                                        [
                                            [
                                                name: 'OS',
                                                values: 'windows'
                                            ],
                                            [
                                                name: 'ARCHITECTURE',
                                                values: 'arm64',
                                            ]
                                        ]
                                    ],
                                    when: {entry -> "INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase() && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]},
                                    stages: [
                                        { entry ->
                                            stage('Test Package') {
                                                node("${entry.OS} && ${entry.ARCHITECTURE} ${['linux', 'windows'].contains(entry.OS) ? '&& docker': ''}"){
                                                    try{
                                                        checkout scm
                                                        unstash 'PYTHON_PACKAGES'
                                                        if(['linux', 'windows'].contains(entry.OS) && params.containsKey("INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()) && params["INCLUDE_${entry.OS}-${entry.ARCHITECTURE}".toUpperCase()]){
                                                            docker.image(env.DEFAULT_PYTHON_DOCKER_IMAGE ? env.DEFAULT_PYTHON_DOCKER_IMAGE: 'python')
                                                                .inside(
                                                                    isUnix() ?
                                                                        '--mount source=tripwire_cache,target=/tmp' :
                                                                        "--mount type=volume,source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython \
                                                                        --mount type=volume,source=pipcache,target=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache \
                                                                        --mount type=volume,source=uv_cache_dir,target=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache"
                                                                ){
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
                                                                                       ./venv/bin/uv python install cpython-${entry.PYTHON_VERSION}
                                                                                       ./venv/bin/uvx -c requirements-dev.txt --with tox-uv  tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                    """
                                                                        )
                                                                    }
                                                                 } else {
                                                                    withEnv([
                                                                        'PIP_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\pipcache',
                                                                        'UV_TOOL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvtools',
                                                                        'UV_PYTHON_INSTALL_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvpython',
                                                                        'UV_CACHE_DIR=C:\\Users\\ContainerUser\\Documents\\cache\\uvcache',
                                                                    ]){
                                                                        powershell(
                                                                            label: 'Testing with tox',
                                                                            script: """python -m venv venv
                                                                                       .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                                       .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                                       .\\venv\\Scripts\\uvx -c requirements-dev.txt --with tox-uv tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                                    """
                                                                        )
                                                                    }
                                                                 }
                                                            }
                                                        } else {
                                                            if(isUnix()){
                                                                sh(
                                                                    label: 'Testing with tox',
                                                                    script: """python3 -m venv venv
                                                                               ./venv/bin/pip install --disable-pip-version-check uv
                                                                               ./venv/bin/uvx -c requirements-dev.txt --with tox-uv tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                            """
                                                                )
                                                            } else {
                                                                bat(
                                                                    label: 'Testing with tox',
                                                                    script: """python -m venv venv
                                                                               .\\venv\\Scripts\\pip install --disable-pip-version-check uv
                                                                               .\\venv\\Scripts\\uv python install cpython-${entry.PYTHON_VERSION}
                                                                               .\\venv\\Scripts\\uvx -c requirements-dev.txt --with tox-uv tox --installpkg ${findFiles(glob: entry.PACKAGE_TYPE == 'wheel' ? 'dist/*.whl' : 'dist/*.tar.gz')[0].path} -e py${entry.PYTHON_VERSION.replace('.', '')}
                                                                            """
                                                                )
                                                            }
                                                        }
                                                    } finally{
                                                        if(isUnix()){
                                                            sh "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        } else {
                                                            bat "${tool(name: 'Default', type: 'git')} clean -dfx"
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                )
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
                        UV_PYTHON_PREFERENCE='only-managed'
                    }
                    parallel{
                        stage('Mac Application Bundle x86_64'){
                            stages{
                                stage('Package'){
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
                                            archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
                                            stash includes: 'dist/*.tar.gz', name: 'APPLE_APPLICATION_X86_64'
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
                                stage('Test'){
                                    agent{
                                        label 'mac && x86_64'
                                    }
                                    options {
                                        skipDefaultCheckout true
                                    }
                                    steps{
                                        unstash 'APPLE_APPLICATION_X86_64'
                                        untar(file: "${findFiles(glob: 'dist/*.tar.gz')[0]}", dir: 'dist/out')
                                        script{
                                            def application = findFiles(glob: 'dist/out/**/tripwire')[0].path
                                            sh "${application} --help"
                                            sh "${application} --version"
                                        }
                                    }
                                    post{
                                        cleanup{
                                           cleanWs(
                                                 deleteDirs: true,
                                                 patterns: [
                                                     [pattern: 'dist/', type: 'INCLUDE'],
                                                 ]
                                             )
                                        }
                                    }
                                }
                            }
                        }
                        stage('Mac Application Bundle arm64'){
                            when{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                                beforeAgent true
                            }
                            stages{
                                stage('Package'){
                                    agent{
                                        label 'mac && python3.12 && arm64'
                                    }
                                    steps{
                                        sh './contrib/create_mac_distrib.sh'
                                    }
                                    post{
                                        success{
                                            archiveArtifacts artifacts: 'dist/*.tar.gz', fingerprint: true
                                            stash includes: 'dist/*.tar.gz', name: 'APPLE_APPLICATION_ARM64'
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
                                stage('Test'){
                                    agent{
                                        label 'mac && arm64'
                                    }
                                    options {
                                        skipDefaultCheckout true
                                    }
                                    steps{
                                        unstash 'APPLE_APPLICATION_ARM64'
                                        untar(file: "${findFiles(glob: 'dist/*.tar.gz')[0]}", dir: 'dist/out')
                                        script{
                                            def application = findFiles(glob: 'dist/out/**/tripwire')[0].path
                                            sh "${application} --help"
                                            sh "${application} --version"
                                        }
                                    }
                                    post{
                                        cleanup{
                                           cleanWs(
                                                 deleteDirs: true,
                                                 patterns: [
                                                     [pattern: 'dist/', type: 'INCLUDE'],
                                                 ]
                                             )
                                        }
                                    }
                                }
                            }
                        }
                        stage('Windows Application'){
                            environment{
                                UV_PYTHON_INSTALL_DIR='C:\\Users\\ContainerUser\\Documents\\uvpython'
                            }
                            when{
                                equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                                beforeAgent true
                            }
                            stages{
                                stage('Package'){
                                    agent{
                                        docker{
                                            image 'python'
                                            label 'windows && docker && x86_64'
                                            args '--mount source=uv_python_install_dir,target=C:\\Users\\ContainerUser\\Documents\\uvpython'
                                        }
                                    }
                                    steps{
                                        bat(script: 'contrib/create_windows_distrib.bat')
                                    }
                                    post{
                                        success{
                                            archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
                                            stash includes: 'dist/*.zip', name: 'WINDOWS_APPLICATION_X86_64'
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
                                stage('Test package'){
                                    agent {
                                        docker {
                                            image 'mcr.microsoft.com/windows/servercore:ltsc2025'
                                            label 'windows && docker && x86_64'
                                        }
                                    }
                                    options {
                                        skipDefaultCheckout true
                                    }
                                    steps{
                                        unstash 'WINDOWS_APPLICATION_X86_64'
                                        unzip(zipFile: "${findFiles(glob: 'dist/*.zip')[0]}", dir: 'dist/tripwire')
                                        script{
                                            def application = findFiles(glob: 'dist/tripwire/**/tripwire.exe')[0]
                                            bat "${application} --help"
                                            bat "${application} --version"
                                        }
                                    }
                                    post{
                                        cleanup{
                                            cleanWs(
                                                deleteDirs: true,
                                                patterns: [
                                                    [pattern: 'dist/', type: 'INCLUDE'],
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
        stage('Deploy'){
            when{
                anyOf{
                    equals expected: true, actual: params.DEPLOY_STANDALONE_PACKAGERS
                    equals expected: true, actual: params.DEPLOY_PYPI
                }
            }
            stages{
                stage('Deploy to pypi') {
                    environment{
                        PIP_CACHE_DIR='/tmp/pipcache'
                        UV_INDEX_STRATEGY='unsafe-best-match'
                        UV_TOOL_DIR='/tmp/uvtools'
                        UV_PYTHON_INSTALL_DIR='/tmp/uvpython'
                        UV_CACHE_DIR='/tmp/uvcache'
                        UV_CONSTRAINT='requirements-dev.txt'
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
                                               uvx -c requirements-dev.txt twine upload --disable-progress-bar --non-interactive dist/*
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
                    parallel{
                        stage('Deploy Standalone Applications: Windows x86_64'){
                            agent any
                            when{
                                equals expected: true, actual: params.PACKAGE_STANDALONE_WINDOWS_INSTALLER
                                beforeAgent true
                            }
                            environment{
                                GENERATED_CHOCOLATEY_CONFIG_FILE='dist/chocolatey/config.json'
                            }
                            steps{
                                script{
                                    unstash 'WINDOWS_APPLICATION_X86_64'
                                    def deploymentFile = findFiles(glob: 'dist/*.zip')[0]
                                    def deployedUrl = deploySingleStandalone(deploymentFile, "${SERVER_URL}/${archiveFolder}", NEXUS_CREDS)
                                    createChocolateyConfigFile(env.GENERATED_CHOCOLATEY_CONFIG_FILE, deploymentFile, deployedUrl)
                                    archiveArtifacts artifacts: env.GENERATED_CHOCOLATEY_CONFIG_FILE
                                    echo "Deployed ${deploymentFile} to ${deployedUrl} -> SHA256: ${sha256(deploymentFile.path)}"
                                }
                            }
                            post{
                                success{
                                    echo "Use ${env.GENERATED_CHOCOLATEY_CONFIG_FILE} for deploying to Chocolatey with https://github.com/UIUCLibrary/chocolatey-hosted-public.git. Found in the artifacts for this build."
                                    echo "${readFile(env.GENERATED_CHOCOLATEY_CONFIG_FILE)}"
                                }
                            }
                        }
                        stage('Deploy Standalone Applications: MacOS ARM64'){
                            agent any
                            when{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_ARM64
                                beforeAgent true
                            }
                            steps{
                                script{
                                    unstash 'APPLE_APPLICATION_ARM64'
                                    def deploymentFile = findFiles(glob: 'dist/*.tar.gz')[0]
                                    def deployedUrl = deploySingleStandalone(deploymentFile, "${SERVER_URL}/${archiveFolder}", NEXUS_CREDS)
                                    echo "Deployed ${deploymentFile} to ${deployedUrl} -> SHA256: ${sha256(deploymentFile.path)}"
                                }
                            }
                        }
                        stage('Deploy Standalone Applications: MacOS X86_64'){
                            agent any
                            when{
                                equals expected: true, actual: params.PACKAGE_MAC_OS_STANDALONE_X86_64
                                beforeAgent true
                            }
                            steps{
                                script{
                                    unstash 'APPLE_APPLICATION_X86_64'
                                    def deploymentFile = findFiles(glob: 'dist/*.tar.gz')[0]
                                    def deployedUrl = deploySingleStandalone(deploymentFile, "${SERVER_URL}/${archiveFolder}", NEXUS_CREDS)
                                    echo "Deployed ${deploymentFile} to ${deployedUrl} -> SHA256: ${sha256(deploymentFile.path)}"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}