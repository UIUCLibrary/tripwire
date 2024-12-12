pipeline {
    agent none
    parameters{
        booleanParam(name: 'RUN_CHECKS', defaultValue: true, description: 'Run checks on code')
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
    }
}