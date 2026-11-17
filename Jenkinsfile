pipeline {
    agent any

    stages {

        stage('Build') {
            steps {
                echo '=== BUILD: preparando el codigo ==='
                sh 'ls -la'
            }
        }

        stage('Test') {
            steps {
                echo '=== TEST: pruebas basicas ==='
                sh 'test -f app.py && echo "app.py encontrado OK"'
                sh 'test -f requirements.txt && echo "requirements.txt encontrado OK"'
            }
        }

        stage('Analyze') {
            steps {
                echo '=== ANALYZE: analisis estatico con SonarQube ==='
                script {
                    def scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv('sonarqube') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Security Test - Dependency Check') {
            steps {
                echo '=== SECURITY TEST: OWASP Dependency-Check ==='
                catchError(buildResult: 'UNSTABLE', stageResult: 'FAILURE') {
                withCredentials([string(credentialsId: 'nvd-api-key', variable: 'NVD_KEY')]) {
                    dependencyCheck(
                        odcInstallation: 'dependency-check',
                        additionalArguments: "--scan ./ --project app-vulnerable --format HTML --format XML --enableExperimental --prettyPrint --nvdApiKey ${NVD_KEY}"
                    )
                }
                }
                dependencyCheckPublisher pattern: '**/dependency-check-report.xml'
            }
        }

        stage('Deploy') {
            steps {
                echo '=== DEPLOY: despliegue de prueba ==='
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'dependency-check-report.*', allowEmptyArchive: true
        }
    }
}
