#!/usr/bin/env groovy
// vim: set ts=4 sts=4 sw=4 noet:

pipeline {
	agent any
	environment {
		DOCKER_IMG = "docker.lco.global/configdb3"
		GIT_COMMIT_SHORT_ID = getCommit().take(12)
		GIT_TAG_NAME = gitTagName()
	}
	stages {
		stage('Build Docker image') {
			steps {
				script {
					dockerImage = docker.build("${DOCKER_IMG}:${GIT_COMMIT_SHORT_ID}", "--pull .")
				}
			}
		}
		stage('Push Docker image') {
			steps {
				script {
					// always push the Docker image with the git commit version
					dockerImage.push()

					if (env.BRANCH_NAME == 'master') {
						// this commit has a git tag associated, push the Docker image
						// with the git tag name as the Docker image tag name
						if (env.GIT_TAG_NAME != null && env.GIT_TAG_NAME != "null") {
							dockerImage.push(env.GIT_TAG_NAME)
						}

						// the master branch always updates the Docker tag "latest" for
						// user convenience purposes
						dockerImage.push('latest')
					}
				}
			}
		}
	}
}

/** @return The tag name, or `null` if the current commit isn't a tag. */
String gitTagName() {
	commit = getCommit()
	if (commit) {
		git_command = "git describe --tags ${commit}"
		return_code = sh(script: git_command, returnStatus: true)
		if (return_code == 0) {
			desc = sh(script: git_command, returnStdout: true)?.trim()
			if (isTag(desc)) {
				return desc
			}
		}
	}
	return null
}

String getCommit() {
	return sh(script: 'git rev-parse HEAD', returnStdout: true)?.trim()
}

@NonCPS
boolean isTag(String desc) {
	match = desc =~ /.+-[0-9]+-g[0-9A-Fa-f]{6,}$/
	result = !match
	match = null // prevent serialisation
	return result
}
