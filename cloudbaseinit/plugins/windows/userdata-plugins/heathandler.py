# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import re
import tempfile
import uuid
import email
import tempfile
import os
import errno
from cloudbaseinit.openstack.common import log as logging
from cloudbaseinit.osutils.factory import *

LOG = logging.getLogger("cloudbaseinit")

def get_plugin(parent_set):
    return HeatUserDataHandler(parent_set)

class HeatUserDataHandler:

    def __init__(self, parent_set):
        LOG.info("Heat user data part handler is loaded.")
        self.type = "text/x-cfninitdata"
        self.name = "Heat userdata plugin"
        return

    def process(self, part):
        #Only user-data part of Heat multipart data is supported. All other cfinitdata part will be skipped
        if part.get_filename() == "cfn-userdata":
            self.handle(part.get_payload())
 
    def handle(self, user_data):

        osutils = OSUtilsFactory().get_os_utils()

        target_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        if re.search(r'^rem cmd\s', user_data, re.I):
            target_path += '.cmd'
            args = [target_path]
            shell = True
        elif re.search(r'^#!', user_data, re.I):
            target_path += '.sh'
            args = ['bash.exe', target_path]
            shell = False
        elif re.search(r'^#ps1\s', user_data, re.I):
            target_path += '.ps1'
            args = ['powershell.exe', '-ExecutionPolicy', 'RemoteSigned',
                    '-NonInteractive', target_path]
            shell = False
        else:
            # Unsupported
            LOG.warning('Unsupported user_data format')
            return False

        try:
            with open(target_path, 'wb') as f:
                f.write(user_data)
            (out, err, ret_val) = osutils.execute_process(args, shell)

            LOG.info('Heat User_data script ended with return code: %d' % ret_val)
            LOG.debug('User_data stdout:\n%s' % out)
            LOG.debug('User_data stderr:\n%s' % err)
        except Exception, ex:
            LOG.warning('An error occurred during user_data execution: \'%s\'' % ex)
        finally:
            if os.path.exists(target_path):
                os.remove(target_path)

        return False