#!/usr/bin/env groovy
// vim: set ts=4 sts=4 sw=4 et:

// Generic docker pipeline, copied below
// LCO Jenkins automated docker container build
//dockerPipeline("docker.lco.global/configdb3")

imageName = "docker.lco.global/configdb3"

pipeline {
        agent any
        stages {
            stage('Build Docker Image') {
                steps {
                    // Build the Docker image. Assumptions:
                    // - The project uses the Git revision control system.
                    // - The Dockerfile is at the top level of the project repository.
                    script {
                        gitRevision = rev()
                        dockerImage = docker.build("${imageName}:${gitRevision}", "--pull .")
                    }
                }
            }

            stage('Test') {
                steps {
                    script {
                        docker.image('mysql:5').withRun('-e "MYSQL_ROOT_PASSWORD=my-secret-pw"') { c ->
                            docker.image('mysql:5').inside("--link ${c.id}:db") {
                                /* Wait until mysql service is up */
                                sh 'while ! mysqladmin ping -hdb --silent; do sleep 1; done'
                            }
                            docker.image('centos:7').inside("--link ${c.id}:db") {
                                /*
                                 * Run some tests which require MySQL, and assume that it is
                                 * available on the host name `db`
                                 */
                                sh 'make check'
                            }
                        }
                    }
                }
            }

            stage('Push Docker Image') {
                steps {
                    script {
                        // Always push the Docker image with the tag set to the git commit
                        // id. This makes it possible for users to test out images which
                        // have been created by a branch, etc.
                        dockerImage.push()

                        // If this commit refers to a Git tag, then we will push out the
                        // same image, but with the Docker tag matching the Git tag.
                        if (isTag()) {
                            dockerImage.push(getTag())
                        }
                    }
                }
            }

            stage('Automated Deployment') {
                steps {
                    script {
                        echo "TODO: We need some more experience with Kubernetes first."
                    }
                }
            }
        }
}

// Retrieve the git short id (12 characters)
def rev() {
    return sh(script: 'git rev-parse --short=12 HEAD', returnStdout: true).trim()
}

// Is this exact commit a git tag?
def isTag() {
    return sh(script: 'git describe --exact-match --tags HEAD 2>/dev/null', returnStatus: true) == 0
}

// If this exact commit is a git tag, then return the tag
def getTag() {
    return sh(script: 'git describe --exact-match --tags HEAD 2>/dev/null', returnStdout: true)?.trim()
}

