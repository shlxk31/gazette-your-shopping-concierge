pipeline {
    agent any

    environment {
        SONARQUBE = 'SonarQube'
        PROJECT_KEY = 'Gazette'
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout Code') {
            steps {
                git branch: 'main',
                url: 'git@github.com:shlxk31/gazette-your-shopping-concierge.git',
                credentialsId: 'git-token'
            }
        }

        stage('SonarQube Analysis') {
            def scannerHome = tool 'SonarScanner';
            steps {
                withSonarQubeEnv() {
                    withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                        sh '''
                            ${scannerHome}/bin/sonar-scanner \
                            -Dsonar.login=$SONAR_AUTH_TOKEN
                        '''
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Build & Run (Docker Compose)') {
            steps {
                sh '''
                docker compose down || true
                docker compose up --build -d
                '''
            }
        }
    }
}