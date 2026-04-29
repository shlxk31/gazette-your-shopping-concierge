pipeline {
    agent any

    environment {
        SONARQUBE = 'SonarQube'
        PROJECT_KEY = 'Gazette'
        DOTENV = credentials('gazette-dotenv')
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
            steps {
                script{
                    def scannerHome = tool 'SonarScanner'
                    echo "DEBUG: The scanner home path is: ${scannerHome}"
                    withSonarQubeEnv() {
                        withCredentials([string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN')]) {
                            sh """
                                ${scannerHome}/bin/sonar-scanner
                            """
                        }
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
            steps{
                sh '''
                cp $DOTENV .env
                docker compose down || true
                docker compose up -d --build
                '''
            }
        }
    }
}