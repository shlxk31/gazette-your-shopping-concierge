pipeline {
    agent any

    environment {
        DOCKER_REPO = "taranjeetkalsispit/gazette"
        PUBLIC_IP = "43.205.214.221"
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

        stage('Build Images') {
            steps {
                sh """
                docker build -t $DOCKER_REPO:frontend ./frontend
                docker build -t $DOCKER_REPO:backend ./backend
                """
            }
        }

        stage('Login to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh """
                    echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                    """
                }
            }
        }

        stage('Push Images') {
            steps {
                sh """
                docker push $DOCKER_REPO:frontend
                docker push $DOCKER_REPO:backend
                """
            }
        }

        stage('Deploy to EC2') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'ec2-ssh-key',
                        keyFileVariable: 'SSH_KEY'
                    ),
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKER_USER',
                        passwordVariable: 'DOCKER_PASS'
                    ),
                    file(
                        credentialsId: 'gazette-dotenv',
                        variable: 'ENV_FILE'
                    )
                ]) {

sh '''
chmod 400 "$SSH_KEY"

ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" ec2-user@$PUBLIC_IP "
mkdir -p /home/ec2-user/app
"

scp -o StrictHostKeyChecking=no -i "$SSH_KEY" "$ENV_FILE" \
ec2-user@$PUBLIC_IP:/home/ec2-user/app/.env

ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" ec2-user@$PUBLIC_IP "
echo '$DOCKER_PASS' | docker login -u '$DOCKER_USER' --password-stdin &&

docker pull $DOCKER_REPO:frontend &&
docker pull $DOCKER_REPO:backend &&

docker stop frontend || true &&
docker rm frontend || true &&
docker stop backend || true &&
docker rm backend || true &&

docker network create gazette-net
docker run -d --env-file /home/ec2-user/app/.env --network gazette-net -p 80:80 --name frontend $DOCKER_REPO:frontend &&
docker run -d --env-file /home/ec2-user/app/.env --network gazette-net -p 5000:5000 --name backend $DOCKER_REPO:backend
"
'''
                }
            }
        }
    }
}