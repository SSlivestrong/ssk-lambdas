properties([
            [
            $class: 'RebuildSettings', autoRebuild: false, rebuildDisabled: false],
           ])

pipeline {
  triggers {
    pollSCM('')
  }
    agent{
        label "Linux"
    } 
 
    environment {
        // this are the credentials so we can: clone repo for dynamic Branch parameter dropdown or if we wanted to gitTag
        GIT_CREDS = credentials("artifactory-sa")      
        // if we initialize an environ Variable  cant be override declarative
        AWS_COMMON_CREDS = credentials('AWS_Credentials_jenkins')
        AWS_DEFAULT_REGION = "us-east-1"
        //ECR REPO
        ECR_REPO_URL="262403030294.dkr.ecr.us-east-1.amazonaws.com"
        //UAT ECR & ECS
        UAT_DCCA_REPO = "262403030294.dkr.ecr.us-east-1.amazonaws.com/uat-rts-dcca-service-repo"
        UAT_TP_REPO = "262403030294.dkr.ecr.us-east-1.amazonaws.com/uat-rts-tp-service-repo"
        UAT_MOCK_HUB_REPO = "262403030294.dkr.ecr.us-east-1.amazonaws.com/uat-rts-mock-hub-service-repo"
        UAT_ECS_CLUSER = "uat-rts"
        //PROD ECR & ECS
        PROD_DCCA_REPO = "262403030294.dkr.ecr.us-east-1.amazonaws.com/prod-rts-dcca-repo"
        PROD_TP_REPO = "262403030294.dkr.ecr.us-east-1.amazonaws.com/prod-rts-tp-repo"
        PROD_MOCK_HUB_REPO = "262403030294.dkr.ecr.us-east-1.amazonaws.com/prod-rts-mock-hub-repo"
        PROD_ECS_CLUSER = "prod-rts"
        //ECS Cluster
        
        // image_url = set_role_and_get_image_url()
    }

    stages {
        stage("Get AWS Credentials"){
            steps{

                script {
                    echo "Getting AWS Credentials"
                    // echo "we running the function"
                    get_credentials_for_a_role("arn:aws:iam::262403030294:role/go-jenkins-role")
                    // echo "env.AWS_ACCESS_KEY_ID is: ${AWS_ACCESS_KEY_ID}"
                    // echo "env.AWS_SECRET_ACCESS_KEY is: ${AWS_SECRET_ACCESS_KEY}"
                    // echo "env.AWS_SESSION_TOKEN is: ${AWS_SESSION_TOKEN}"
                    // echo "we finish the function"
                    // sh "aws sts get-caller-identity" 
                }
            }
        }

        stage('Preparation') {
            when {
                 expression { currentBuild.currentResult == "SUCCESS" }
            }
            steps {
                cleanWs()
                echo "${JOB_NAME}"
                echo env.docker_full_tag
                echo env.docker_file_path
                sh 'env'
                sh 'docker --version'
                sh 'pip3 --version'
                sh 'aws ecr --version'
                sh "ecs-cli --version"

                echo "Git Branch/Tag: ${env.branch_name}"

                script{
                    if("${env.branch_name}" == ""){
                        print("Branch param is empty please type the branch or gitTag you want to build")
                        currentBuild.result = "FAILURE"
                        sh "error 1"
                    }     
                }

                checkout scm

                // checkout([$class: 'GitSCM',
                //     branches: [[name: "${env.branch_name}"]],                   
                //     extensions: [],
                //     poll: true,
                //     userRemoteConfigs: [[credentialsId: 'artifactory-sa',
                //     url: "${env.repo_url}"]]]                    
                // )
            }
        }

        //  stage("Run Regression Test Suite"){
        //     when {
        //          expression {  currentBuild.currentResult == "SUCCESS" }
        //     }
        //     steps{
        //         withCredentials([file(credentialsId: 'uat_bastion.pem', variable: 'UAT_SSH')]) {
        //             script {
        //             sh 'cp $UAT_SSH uat.pem'

        //             sh 'chmod 600 uat.pem'

        //             sh '''
        //                 ssh -i uat.pem -o StrictHostKeyChecking=no ec2-user@10.30.140.252 'curl -vvv -k internal-uat-rts-us-east-1-alb-1671185102.us-east-1.elb.amazonaws.com:443/'
        //             '''
        //             }
        //         }
        //     }
        // }

        stage("Build Datacloak Consumer App Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS"}
            }
            steps{
                
                script {
                echo  "Publishing image to AWS ECR"

                sh "aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin  ${env.ECR_REPO_URL}"
                

                if (env.GIT_BRANCH == 'feature/testfusion') {
                    sh "docker build --progress=plain --tag ${env.UAT_DCCA_REPO}:${env.GIT_COMMIT} ./regression_test_suite -f  ./regression_test_suite/Dockerfile.uat-dcca-service --no-cache"
                    sh "docker push ${env.UAT_DCCA_REPO}:${env.GIT_COMMIT}"
                    sh "docker tag ${env.UAT_DCCA_REPO}:${env.GIT_COMMIT} ${env.UAT_DCCA_REPO}:latest"
                    sh "docker push ${env.UAT_DCCA_REPO}:latest"
                }

                if (env.GIT_BRANCH == 'master') {
                    sh "docker build --progress=plain --tag ${env.PROD_DCCA_REPO}:${env.GIT_COMMIT} ./regression_test_suite -f  ./regression_test_suite/Dockerfile.prod-dcca-service --no-cache"
                    sh "docker push ${env.PROD_DCCA_REPO}:${env.GIT_COMMIT}"
                    sh "docker tag ${env.PROD_DCCA_REPO}:${env.GIT_COMMIT} ${env.PROD_DCCA_REPO}:latest"
                    sh "docker push ${env.PROD_DCCA_REPO}:latest"
                }
                }
            }
        }

        stage("Build Test Pilot Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS"}
            }
            steps{

                script {
                echo  "Publishing image to AWS ECR"

                sh "aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin  ${env.ECR_REPO_URL}"
                
                if (env.GIT_BRANCH == 'feature/testfusion') {
                        sh "docker build --progress=plain --tag ${env.UAT_TP_REPO}:${env.GIT_COMMIT} ./regression_test_suite -f  ./regression_test_suite/Dockerfile.uat-tp-service --no-cache"
                        sh "docker push ${env.UAT_TP_REPO}:${env.GIT_COMMIT}"
                        sh "docker tag ${env.UAT_TP_REPO}:${env.GIT_COMMIT} ${env.UAT_TP_REPO}:latest"
                        sh "docker push ${env.UAT_TP_REPO}:latest"
                }

                if (env.GIT_BRANCH == 'master') {
                    sh "docker build --progress=plain --tag ${env.PROD_TP_REPO}:${env.GIT_COMMIT} ./regression_test_suite -f  ./regression_test_suite/Dockerfile.prod-tp-service --no-cache"
                    sh "docker push ${env.PROD_TP_REPO}:${env.GIT_COMMIT}"
                    sh "docker tag ${env.PROD_TP_REPO}:${env.GIT_COMMIT} ${env.PROD_TP_REPO}:latest"
                    sh "docker push ${env.PROD_TP_REPO}:latest"
                }
                }
            } 
        }

        stage("Build Mockhub Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS"}
            }
            steps{
                
                script {
                echo  "Publishing image to AWS ECR"

                sh "aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin  ${env.ECR_REPO_URL}"

                if (env.GIT_BRANCH == 'feature/testfusion') {
                        sh "docker build --progress=plain --tag ${env.UAT_MOCK_HUB_REPO}:${env.GIT_COMMIT} ./regression_test_suite -f ./regression_test_suite/Dockerfile.uat-mock-hub-service --no-cache"
                        sh "docker push ${env.UAT_MOCK_HUB_REPO}:${env.GIT_COMMIT}"
                        sh "docker tag ${env.UAT_MOCK_HUB_REPO}:${env.GIT_COMMIT} ${env.UAT_MOCK_HUB_REPO}:latest"
                        sh "docker push ${env.UAT_MOCK_HUB_REPO}:latest"
                }

                if (env.GIT_BRANCH == 'master') {
                    sh "docker build --progress=plain --tag ${env.PROD_MOCK_HUB_REPO}:${env.GIT_COMMIT} ./regression_test_suite -f ./regression_test_suite/Dockerfile.prod-mock-hub-service --no-cache"
                    sh "docker push ${env.PROD_MOCK_HUB_REPO}:${env.GIT_COMMIT}"
                    sh "docker tag ${env.PROD_MOCK_HUB_REPO}:${env.GIT_COMMIT} ${env.PROD_MOCK_HUB_REPO}:latest"
                    sh "docker push ${env.PROD_MOCK_HUB_REPO}:latest"
                }
                }
            }
        }


        stage("Deploy UAT Datacloak Consumer App Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS" && env.GIT_BRANCH == 'feature/testfusion' }
            }
            steps{
                
                script {

                sh "aws ecs update-service --cluster uat-rts --service uat-rts-dcca-service --force-new-deployment"
               
                }
            }
        }

        stage("Deploy PROD Datacloak Consumer App Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS" && env.GIT_BRANCH == 'master' }
            }
            steps{
                
                script {

                sh "aws ecs update-service --cluster ${env.PROD_ECS_CLUSER} --service prod-rts-dcca --force-new-deployment"
               
                }
            }
        }

        stage("Deploy UAT Test Pilot Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS" && env.GIT_BRANCH == 'feature/testfusion' }
            }
            steps{
                
                script {

                sh "aws ecs update-service --cluster uat-rts --service uat-rts-tp-service --force-new-deployment"
               
                }
            }
        }

        stage("Deploy PROD Test Pilot Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS" && env.GIT_BRANCH == 'master' }
            }
            steps{
                
                script {

                sh "aws ecs update-service --cluster ${env.PROD_ECS_CLUSER} --service prod-rts-tp --force-new-deployment"
               
                }
            }
        }

        stage("Deploy UAT Mockhub Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS" && env.GIT_BRANCH == 'feature/testfusion' }
            }
            steps{
                
                script {

                sh "aws ecs update-service --cluster uat-rts --service uat-rts-mock-hub-service --force-new-deployment"
               
                }
            }
        }

        stage("Deploy PROD Mockhub Service"){
            when {
                 expression {  currentBuild.currentResult == "SUCCESS" && env.GIT_BRANCH == 'master' }
            }
            steps{
                
                script {

                sh "aws ecs update-service --cluster ${env.PROD_ECS_CLUSER} --service prod-rts-mockhub --force-new-deployment"
               
                }
            }
        }

                
    //     stage('Pytest Execution'){
    //         when {
    //              expression { currentBuild.currentResult == "SUCCESS" && params.run_tests==true }
    //         }
    //         steps{
             
    //             sh '''#!/bin/bash -ex
                
    //                 echo "setting up pytest"
                    
    //                 PYTHON_VERSION="$(echo $python_version | cut -d " " -f 2 | cut -d "." -f 1-2)"

    //                 VIRTUAL_ENV_NAME='py-virtual-env'
    //                 echo "Virtual Env: "$VIRTUAL_ENV_NAME
    //                 python$PYTHON_VERSION -m venv $VIRTUAL_ENV_NAME

    //                 echo "setting up source"
    //                 source $VIRTUAL_ENV_NAME/bin/activate

    //                 echo "PYTHONPATH is :"$PATH
    //                 currentpath=$(pwd)
    //                 export PATH=$currentpath:$PATH
    //                 echo "after export PYTHONPATH is :"$PATH
                    
    //                 echo "currentpath is :"$currentpath
                    
    //                 cd src/
                    
    //                 python$PYTHON_VERSION -m pip install --upgrade pip
                    
    //                 pip3 install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org --proxy http://usalnp-proxy.aln.experian.com:9090
                    
    //                 echo "requirements file installed"
                    
    //                 echo "Running test classes"
                    
    //                 testPath=$currentpath/tests
    //                 coverageSourcesPath=$currentpath/src
    //                 coverage_path=$WORKSPACE/coverage_report
    //                 echo "coverage_path $coverage_path"
    //                 config_coverage_path=$currentpath/.coverage_rc
    //                 echo "config_coverage_path $config_coverage_path"
    //                 python$PYTHON_VERSION -m pytest --cov-report html:$coverage_path $testPath --cov=$coverageSourcesPath -p no:warnings --cov-config=$config_coverage_path --cov-fail-under=70 -s -vv
                    
    //                 echo "Pytest execution completed"
    //                 echo "deactivating virtual env"
    //                 deactivate
    //             '''
    //         }
    //     }
        
    //     stage('Publish Coverage Report') {
    //         when {
    //              expression { currentBuild.currentResult == "SUCCESS" && params.run_tests==true }
    //         }
	// 	    steps {
	// 			script {
    //                 publishHTML([allowMissing: true, alwaysLinkToLastBuild: true, keepAll: true, reportDir: "${WORKSPACE}/coverage_report", reportFiles: 'index.html', reportName: 'Ascend Ops Platform Python Coverage', reportTitles: 'Ascend OPS Platform Python Coverage'])
    //               }
    //         }
	// 	}
    //     stage("Build Push Docker 'Latest'"){
    //         when {
    //              expression {  currentBuild.currentResult == "SUCCESS" && params.push_to_latests == true}
    //         }
    //         steps{
    //             echo  "Publishing image to AWS ECR:latest"
    //             // echo "start docker build :latest"

    //             // we build the image from scratch since we had to Dockerfile one for testing and the other with out the testing files
    //             sh "aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin  ${env.image_url}"

    //             //for alex aws image
    //             sh "docker build --progress=plain --build-arg env=${env.deployment_environment} --build-arg PYTHON_ENV=${env.deployment_environment} --build-arg account_id=${env.account_id} --build-arg PYTHON_VERSION=${env.python_version} --build-arg NGINX_PORT=${env.nginx_port} --build-arg HTTP_PROXY=${http_proxy} --build-arg HTTPS_PROXY=${https_proxy} --tag ${env.docker_full_tag_latest} --file ${env.docker_file_path} ${WORKSPACE} --no-cache"

    //             sh "docker push ${env.docker_full_tag_latest}"
    //             echo "finish pushing docker_full_tag_latest: ${env.docker_full_tag_latest}"
    //         }
    //     }
    //     stage("Get ID of docker group"){
    //         when {
    //              expression { currentBuild.currentResult == "SUCCESS" && params.push_to_latests == true }
    //         }
    //         steps {
    //             script {
    //                 docker_gid = sh(script: 'getent group docker | cut -d: -f3', returnStdout: true).trim()
    //                     }
    //                 }
    //         }
    //     stage('Wiz Scan in Container Agent') {
    //         when {
    //              beforeAgent true
    //              expression { currentBuild.currentResult == "SUCCESS" && params.push_to_latests == true }
    //         }
    //         agent {
    //             docker {
    //                 image 'artifacts.experian.local/wizcli-remote/wizcli:latest'
    //                 args "--group-add $docker_gid --mount type=bind,src=$WORKSPACE,dst=/cli --mount type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock --entrypoint="
    //                 reuseNode true
    //             }
    //         }
    //         steps {
    //             withCredentials([usernamePassword(credentialsId: 'wiz-sa', usernameVariable: 'ID', passwordVariable: 'SECRET')])
    //             {
    //             sh '/entrypoint auth --id $ID --secret $SECRET'
    //             sh "/entrypoint docker scan --image \"${env.docker_full_tag_latest}\" --show-vulnerability-details --tag usage=common-base-image"
    //             }
    //         }
    //     }
	// 	stage("Update Cluster Service IN ECS"){
    //         when {
    //              expression { currentBuild.currentResult == "SUCCESS" && params.update_service == true }
    //         }
    //         steps{
	// 			script {
	// 				echo "Updating service: ${env.service_name} in cluster: ${env.cluster_name}"					
	// 				def update_service_ecs = "aws ecs update-service --cluster ${env.task_definition_cluster} --service ${env.service_name} --task-definition ${env.task_definition} --force-new-deployment"
	// 				def strResponse = sh (script:update_service_ecs, returnStdout: true)
					
	// 				echo "Sleeping for 5 min while we turn on the ECS task and let it run the entrypoint"
	// 				sleep(time:5, unit:"MINUTES")
				
	// 				def jsonResponse = readJSON text: strResponse
    //                 print(jsonResponse)
	// 				def desiredCount = jsonResponse.service.desiredCount
	// 				print("Desired Count: " + desiredCount)
	// 				def runningCount = jsonResponse.service.runningCount
	// 				print("Running Count: " + runningCount)
					
	// 				if (desiredCount.equals(runningCount)) {
	// 					echo "Updated service: ${env.service_name} in cluster: ${env.clusterName} successfully"
	// 				}
	// 			}
    //         }
    //     }
	// }
	// post {        
    //     success{
    //         echo "is Successful, sending email: ${JOB_NAME}  ${BUILD_URL}"
    //         echo  "Job '${JOB_NAME}' (${BUILD_NUMBER})"
            
    //          emailext attachLog: true,
    //                  body: "${currentBuild.currentResult}: Job ${env.JOB_NAME} build ${env.BUILD_NUMBER}\n More info at: ${env.BUILD_URL}",
    //                   to: "poonam.argarwal@experian.com",
    //                   subject: "${JOB_NAME} ${BUILD_NUMBER} success" 
    //     }

    //     unsuccessful {
    //         echo "is unsuccessful, sending email: ${JOB_NAME}  ${BUILD_URL}"
    //         echo  "Job '${JOB_NAME}' (${BUILD_NUMBER})"

    //          emailext attachLog: true,
    //                  body: "${currentBuild.currentResult}: Job ${env.JOB_NAME} build ${env.BUILD_NUMBER}\n More info at: ${env.BUILD_URL}",
    //                   to: "poonam.argarwal@experian.com",
    //                   subject: "${JOB_NAME} ${BUILD_NUMBER} unsuccessful"

    //     }
    // }
}

}

           
def get_credentials_for_a_role(the_role_string) {
    print("this is the function")
    print(the_role_string)
    print("obfuscated user and password")
    print(env.AWS_COMMON_CREDS_USR)
    print(env.AWS_COMMON_CREDS_PSW)
	def encPassword=(env.AWS_COMMON_CREDS_PSW).bytes.encodeBase64().toString()
    def json = '{"role": "' + the_role_string +'","isInternal": true,"username": "' + env.AWS_COMMON_CREDS_USR + '"}'
    def url = "curl -vvv -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' --header 'Authorization: " + encPassword + "' --header 'Connection: closed' -d '" + json + "' 'http://internal-stsserv-451674942.us-east-1.elb.amazonaws.com/generate/user'"
    def strResponse = sh (script:url, returnStdout: true)

    def jsonResponse = readJSON text: strResponse

    if (jsonResponse.code){
        print("found code error in the STS API responds")
        print(jsonResponse.message)
        currentBuild.result = 'FAILURE'
        sh "exit 1"
    }
    else{
        print("code error was not found in the STS API responds and we got the aws credentials") 
        env.AWS_ACCESS_KEY_ID = jsonResponse.accessKeyId
        print("accessKeyId:")
        print(jsonResponse.accessKeyId)
        env.AWS_SECRET_ACCESS_KEY = jsonResponse.secretAccessKey
        env.AWS_SESSION_TOKEN = jsonResponse.sessionToken
        currentBuild.result = 'SUCCESS'
    }
}