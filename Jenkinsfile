// =====================================================================
//  PIPELINE DEVSECOPS - Guia 3.2.2 Pruebas Automatizadas
//  Etapas: Build -> Test -> Analyze -> Deploy -> Security Test
//  Herramientas: SonarQube (SAST) | Dependency-Check (SCA) | ZAP (DAST)
// =====================================================================

pipeline {
    agent any

    environment {
        TARGET_URL = 'http://app-vulnerable:5000'
        ZAP_URL    = 'http://zap:8090'
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        // -------------------------------------------------------------
        // 1. BUILD - Preparacion del codigo
        // -------------------------------------------------------------
        stage('Build') {
            steps {
                echo '=== BUILD: preparando el codigo fuente ==='
                sh '''
                    echo "Rama:    $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
                    echo "Commit:  $(git rev-parse --short HEAD)"
                    echo "--- Contenido del proyecto ---"
                    ls -la
                '''
            }
        }

        // -------------------------------------------------------------
        // 2. TEST - Pruebas unitarias y basicas
        // -------------------------------------------------------------
        stage('Test') {
            steps {
                echo '=== TEST: pruebas unitarias y de integridad ==='
                sh '''
                    echo "--- Verificacion de archivos del proyecto ---"
                    test -f app.py                     && echo "[OK] app.py"
                    test -f requirements.txt           && echo "[OK] requirements.txt"
                    test -f Dockerfile                 && echo "[OK] Dockerfile"
                    test -f sonar-project.properties   && echo "[OK] sonar-project.properties"

                    echo ""
                    echo "--- Pruebas unitarias ---"
                    if command -v python3 >/dev/null 2>&1; then
                        python3 -m unittest discover -v -p "test_*.py"
                    else
                        echo "[AVISO] python3 no disponible; se omiten las pruebas unitarias"
                    fi
                '''
            }
        }

        // -------------------------------------------------------------
        // 3. ANALYZE - Analisis estatico SAST con SonarQube
        // -------------------------------------------------------------
        stage('Analyze') {
            steps {
                echo '=== ANALYZE: analisis estatico de calidad y seguridad (SonarQube) ==='
                script {
                    def scannerHome = tool 'sonar-scanner'
                    withSonarQubeEnv('sonarqube') {
                        sh "${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        // -------------------------------------------------------------
        // 4. DEPLOY - Despliegue en entorno de prueba accesible para ZAP
        //    Va antes del DAST porque ZAP necesita la app en ejecucion
        // -------------------------------------------------------------
        stage('Deploy') {
            steps {
                echo '=== DEPLOY: validando el entorno de prueba ==='
                sh '''
                    echo "Entorno de prueba: $TARGET_URL"
                    curl -s -o /dev/null -w "Codigo HTTP de la app: %{http_code}\\n" $TARGET_URL/
                    echo "--- Respuesta del endpoint vulnerable ---"
                    curl -s "$TARGET_URL/hello?name=DeployCheck"
                    echo ""
                    echo "[OK] Aplicacion desplegada y accesible para el analisis dinamico"
                '''
            }
        }

        // -------------------------------------------------------------
        // 5a. SECURITY TEST (SCA) - OWASP Dependency-Check
        // -------------------------------------------------------------
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

        // -------------------------------------------------------------
        // 5b. SECURITY TEST (DAST) - OWASP ZAP
        // -------------------------------------------------------------
        stage('Security Test - OWASP ZAP') {
            steps {
                echo '=== SECURITY TEST (DAST): OWASP ZAP ==='
                sh '''
                    set -e

                    echo "--- 1. Accediendo a la URL objetivo ---"
                    curl -s "$ZAP_URL/JSON/core/action/accessUrl/?url=$TARGET_URL/" > /dev/null

                    echo "--- 2. Spider: descubrimiento de rutas ---"
                    SPIDER_ID=$(curl -s "$ZAP_URL/JSON/spider/action/scan/?url=$TARGET_URL&recurse=true" | grep -o '[0-9]\\+')
                    while true; do
                        ST=$(curl -s "$ZAP_URL/JSON/spider/view/status/?scanId=$SPIDER_ID" | grep -o '[0-9]\\+')
                        echo "    Spider: $ST%"
                        [ "$ST" = "100" ] && break
                        sleep 3
                    done

                    echo "--- 3. Alimentando endpoints con parametros ---"
                    curl -s "$ZAP_URL/JSON/core/action/accessUrl/?url=$TARGET_URL/hello%3Fname%3Dtest" > /dev/null

                    echo "--- 4. Active Scan: busqueda activa de vulnerabilidades ---"
                    SCAN_ID=$(curl -s "$ZAP_URL/JSON/ascan/action/scan/?url=$TARGET_URL&recurse=true&inScopeOnly=false" | grep -o '[0-9]\\+')
                    while true; do
                        ST=$(curl -s "$ZAP_URL/JSON/ascan/view/status/?scanId=$SCAN_ID" | grep -o '[0-9]\\+')
                        echo "    Active Scan: $ST%"
                        [ "$ST" = "100" ] && break
                        sleep 5
                    done

                    echo "--- 5. Generando reportes ---"
                    curl -s "$ZAP_URL/OTHER/core/other/htmlreport/" -o zap-report.html
                    curl -s "$ZAP_URL/JSON/core/view/alerts/?baseurl=$TARGET_URL" -o zap-alerts.json

                    echo "--- 6. Resumen de alertas detectadas ---"
                    curl -s "$ZAP_URL/JSON/alert/view/alertsSummary/?baseurl=$TARGET_URL"
                    echo ""
                '''
            }
        }
    }

    // -----------------------------------------------------------------
    // POST - Publicacion de reportes
    // -----------------------------------------------------------------
    post {
        always {
            echo '=== Archivando reportes de seguridad ==='
            archiveArtifacts artifacts: 'dependency-check-report.*, zap-report.html, zap-alerts.json',
                             allowEmptyArchive: true
        }
        success {
            echo 'PIPELINE COMPLETADO: todas las etapas finalizaron correctamente.'
        }
        unstable {
            echo 'PIPELINE INESTABLE: revisar los hallazgos de seguridad reportados.'
        }
        failure {
            echo 'PIPELINE FALLIDO: revisar el log de la etapa con error.'
        }
    }
}
