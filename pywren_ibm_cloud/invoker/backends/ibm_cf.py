#
# Copyright 2018 PyWren Team
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import time
import logging
import random
from pywren_ibm_cloud.utils import format_action_name
from pywren_ibm_cloud.wrenconfig import extract_cf_config
from pywren_ibm_cloud.libs.ibm.cloudfunctions_client import CloudFunctionsClient
from pywren_ibm_cloud.version import __version__


logger = logging.getLogger(__name__)


class IBMCloudFunctionsInvoker:

    def __init__(self, config):
        self.log_level = os.getenv('PYWREN_LOG_LEVEL')
        self.namespace = config['ibm_cf']['namespace']
        self.endpoint = config['ibm_cf']['endpoint'].replace('http:', 'https:')
        self.runtime_name = config['pywren']['runtime']
        self.runtime_memory = int(config['pywren']['runtime_memory'])
        self.runtime_timeout = int(config['pywren']['runtime_timeout'])
        self.package = 'pywren_v'+__version__

        self.invocation_retry = config['pywren']['invocation_retry']
        self.retry_sleeps = config['pywren']['retry_sleeps']
        self.retries = config['pywren']['retries']

        self.cf_client = CloudFunctionsClient(extract_cf_config(config))

    def invoke(self, payload, runtime_memory):
        """
        Invoke -- return information about this invocation
        """
        self.runtime_memory = runtime_memory
        action_name = format_action_name(self.runtime_name, self.runtime_memory)
        act_id = self.cf_client.invoke(self.package, action_name, payload)
        attempts = 1

        while not act_id and self.invocation_retry and attempts < self.retries:
            attempts += 1
            selected_sleep = random.choice(self.retry_sleeps)
            exec_id = payload['executor_id']
            call_id = payload['call_id']
            log_msg = ('ExecutorID {} - Function {} - Retry {} in {} seconds'.format(exec_id, call_id, attempts, selected_sleep))
            logger.debug(log_msg)
            time.sleep(selected_sleep)
            act_id = self.cf_client.invoke(self.package, action_name, payload)

        return act_id

    def config(self):
        """
        Return config dict
        """
        return {'runtime': self.runtime_name,
                'runtime_memory': self.runtime_memory,
                'runtime_timeout': self.runtime_timeout,
                'namespace': self.namespace,
                'endpoint': self.endpoint}
