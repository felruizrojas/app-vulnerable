pipeline {
    agent any

    environment {
        TARGET_URL = 'http://app-vulnerable:5000'
        ZAP_URL    = 'http://zap:8090'
    }

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

        stage('Deploy') {
            steps {
                echo '=== DEPLOY: verificando entorno de prueba ==='
                sh 'curl -s -o /dev/null -w "App desplegada, codigo HTTP: %{http_code}\\n" $TARGET_URL/'
                sh 'curl -s "$TARGET_URL/hello?name=DeployCheck"'
            }
        }

        stage('Security Test - Dependency Check') {
            steps {
                echo '=== SECURITY TEST (SCA): OWASP Dependency-Check ==='
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

        stage('Security Test - OWASP ZAP') {
            steps {
                echo '=== SECURITY TEST (DAST): OWASP ZAP ==='
                sh '''
                    set -e

                    echo "--- 1. Accediendo a la URL objetivo ---"
                    curl -s "$ZAP_URL/JSON/core/action/accessUrl/?url=$TARGET_URL/" > /dev/null

                    echo "--- 2. Spider (descubrimiento de rutas) ---"
                    SPIDER_ID=$(curl -s "$ZAP_URL/JSON/spider/action/scan/?url=$TARGET_URL&recurse=true" | grep -o '[0-9]\\+')
                    echo "Spider iniciado con ID: $SPIDER_ID"
                    while true; do
                        ST=$(curl -s "$ZAP_URL/JSON/spider/view/status/?scanId=$SPIDER_ID" | grep -o '[0-9]\\+')
                        echo "   Spider: $ST%"
                        [ "$ST" = "100" ] && break
                        sleep 3
                    done

                    echo "--- 3. Alimentando rutas con parametros ---"
                    curl -s "$ZAP_URL/JSON/core/action/accessUrl/?url=$TARGET_URL/hello%3Fname%3Dtest" > /dev/null

                    echo "--- 4. Active Scan (busqueda activa de vulnerabilidades) ---"
                    SCAN_ID=$(curl -s "$ZAP_URL/JSON/ascan/action/scan/?url=$TARGET_URL&recurse=true&inScopeOnly=false" | grep -o '[0-9]\\+')
                    echo "Active Scan iniciado con ID: $SCAN_ID"
                    while true; do
                        ST=$(curl -s "$ZAP_URL/JSON/ascan/view/status/?scanId=$SCAN_ID" | grep -o '[0-9]\\+')
                        echo "   Active Scan: $ST%"
                        [ "$ST" = "100" ] && break
                        sleep 5
                    done

                    echo "--- 5. Generando reportes ---"
                    curl -s "$ZAP_URL/OTHER/core/other/htmlreport/" -o zap-report.html
                    curl -s "$ZAP_URL/JSON/core/view/alerts/?baseurl=$TARGET_URL" -o zap-alerts.json

                    echo "--- 6. Resumen de alertas ---"
                    curl -s "$ZAP_URL/JSON/alert/view/alertsSummary/?baseurl=$TARGET_URL"
                    echo ""
                    ls -lh zap-report.html
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'dependency-check-report.*, zap-report.html, zap-alerts.json', allowEmptyArchive: true
        }
    }
}
