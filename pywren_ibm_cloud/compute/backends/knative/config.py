import sys
from pywren_ibm_cloud.utils import version_str

DOCKER_REPO_DEFAULT = 'docker.io'
RUNTIME_DEFAULT_35 = '<USER>/pywren-kn-runtime-v35'
RUNTIME_DEFAULT_36 = '<USER>/pywren-kn-runtime-v36'
RUNTIME_DEFAULT_37 = '<USER>/pywren-kn-runtime-v37'

GIT_URL_DEFAULT = 'https://github.com/pywren/pywren-ibm-cloud'
GIT_REV_DEFAULT = 'master'

RUNTIME_TIMEOUT_DEFAULT = 600  # 10 minutes
RUNTIME_MEMORY_DEFAULT = 256  # 256Mi

secret_res = """
apiVersion: v1
kind: Secret
metadata:
  name: dockerhub-user-token
  annotations:
    tekton.dev/docker-0: https://index.docker.io/v1/
type: kubernetes.io/basic-auth
stringData:
  username: USER
  password: TOKEN
"""

account_res = """
apiVersion: v1
kind: ServiceAccount
metadata:
  name: pywren-build-pipeline
secrets:
- name: dockerhub-user-token
"""

git_res = """
apiVersion: tekton.dev/v1alpha1
kind: PipelineResource
metadata:
  name: pywren-git
spec:
  type: git
  params:
    - name: revision
      value: master
    - name: url
      value: https://github.com/pywren/pywren-ibm-cloud
"""

task_def = """
apiVersion: tekton.dev/v1alpha1
kind: Task
metadata:
  name: git-source-to-image
spec:
  inputs:
    resources:
      - name: git-source
        type: git
    params:
      - name: pathToContext
        description: Path to build context, within the workspace used by Kaniko
        default: .
      - name: pathToDockerFile
        description: Relative to the context
        default: Dockerfile
      - name: imageUrl
      - name: imageTag
  steps:
    - name: build-and-push
      image: gcr.io/kaniko-project/executor
      env:
        - name: "DOCKER_CONFIG"
          value: "/builder/home/.docker/"
      command:
        - /kaniko/executor
      args:
        - --dockerfile=${inputs.params.pathToDockerFile}
        - --destination=${inputs.params.imageUrl}:${inputs.params.imageTag}
        - --context=/workspace/git-source/${inputs.params.pathToContext}
"""

task_run = """
apiVersion: tekton.dev/v1alpha1
kind: TaskRun
metadata:
  name: image-from-git
spec:
  taskRef:
    name: git-source-to-image
  inputs:
    resources:
      - name: git-source
        resourceRef:
          name: pywren-git
    params:
      - name: pathToContext
        value: .
      - name: pathToDockerFile
        value: runtime/knative/Dockerfile
  serviceAccount: pywren-build-pipeline
"""


service_res = """
apiVersion: serving.knative.dev/v1alpha1
kind: Service
metadata:
  name: pywren-runtime
  #namespace: default
spec:
  template:
    metadata:
      labels:
        type: pywren-runtime
      #annotations:
        # Target 1 in-flight-requests per pod.
        #autoscaling.knative.dev/target: "1"
        #autoscaling.knative.dev/minScale: "0"
        #autoscaling.knative.dev/maxScale: "1000"
    spec:
      containerConcurrency: 1
      timeoutSeconds: TIMEOUT
      container:
        image: IMAGE
        resources:
          limits:
            memory: MEMORY
            #cpu: 1000m
"""


def load_config(config_data):

    required_keys = ('docker_user', 'docker_token')
    if not set(required_keys) <= set(config_data['knative']):
        raise Exception('You must provide {} to access to Knative'.format(required_keys))

    if 'runtime_memory' not in config_data['pywren']:
        config_data['pywren']['runtime_memory'] = RUNTIME_MEMORY_DEFAULT
    if 'runtime_timeout' not in config_data['pywren']:
        config_data['pywren']['runtime_timeout'] = RUNTIME_TIMEOUT_DEFAULT

    if 'docker_repo' not in config_data['knative']:
        config_data['knative']['docker_repo'] = DOCKER_REPO_DEFAULT

    if 'runtime' not in config_data['pywren']:
        docker_user = config_data['knative']['docker_user']
        this_version_str = version_str(sys.version_info)
        if this_version_str == '3.5':
            config_data['pywren']['runtime'] = RUNTIME_DEFAULT_35.replace('<USER>', docker_user)
        elif this_version_str == '3.6':
            config_data['pywren']['runtime'] = RUNTIME_DEFAULT_36.replace('<USER>', docker_user)
        elif this_version_str == '3.7':
            config_data['pywren']['runtime'] = RUNTIME_DEFAULT_37.replace('<USER>', docker_user)
