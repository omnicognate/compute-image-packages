#!/usr/bin/python
# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manage the retrieval and excution of metadata scripts."""

import contextlib
import logging.handlers
import shutil
import sys
import tempfile

from google_compute_engine import config_manager
from google_compute_engine import logger

from google_compute_engine.metadata_scripts import script_executor
from google_compute_engine.metadata_scripts import script_retriever


@contextlib.contextmanager
def _CreateTempDir(prefix):
  """Context manager for creating a temporary directory.

  Args:
    prefix: string, the prefix for the temporary directory.

  Yields:
    string, the temporary directory created.
  """
  temp_dir = tempfile.mkdtemp(prefix=prefix + '-')
  try:
    yield temp_dir
  finally:
    shutil.rmtree(temp_dir)


class ScriptManager(object):
  """A class for retrieving and executing metadata scripts."""

  def __init__(self, script_type):
    """Constructor.

    Args:
      script_type: string, the metadata script type to run.
    """
    self.script_type = script_type
    name = '%s-script' % self.script_type
    facility = logging.handlers.SysLogHandler.LOG_DAEMON
    self.logger = logger.Logger(name=name, facility=facility)
    self.retriever = script_retriever.ScriptRetriever(self.logger, script_type)
    self.executor = script_executor.ScriptExecutor(self.logger, script_type)
    self._RunScripts()

  def _RunScripts(self):
    with _CreateTempDir(self.script_type) as dest_dir:
      try:
        self.logger.info('Starting %s scripts.', self.script_type)
        script_dict = self.retriever.GetScripts(dest_dir)
        self.executor.RunScripts(script_dict)
      finally:
        self.logger.info('Finished running %s scripts.', self.script_type)


def main(args):
  script_types = ('startup', 'shutdown')
  if args and args[0].lower() in script_types:
    script_type = args[0].lower()
  else:
    valid_args = ', '.join(script_types)
    message = 'No valid argument specified. Options: [%s].' % valid_args
    raise ValueError(message)

  instance_config = config_manager.ConfigManager()
  if instance_config.GetOptionBool('MetadataScripts', script_type):
    ScriptManager(script_type)


if __name__ == '__main__':
  main(sys.argv[1:])
