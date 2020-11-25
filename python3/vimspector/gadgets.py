# vimspector - A multi-language debugging system for Vim
# Copyright 2020 Ben Jackson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from vimspector import installer
import sys
import os
import pkgutil
import importlib

def InstallDebugpy( name, root, gadget ):
  wd = os.getcwd()
  root = os.path.join( root, 'debugpy-{}'.format( gadget[ 'version' ] ) )
  os.chdir( root )
  try:
    CheckCall( [ sys.executable, 'setup.py', 'build' ] )
  finally:
    os.chdir( wd )

  MakeSymlink( name, root )


import vimspector.plugins

LOADED = 0
GADGETS = {}

def RegisterGadget( name, spec ):
  GADGETS[ name ] = spec


def Gadgets():
  global LOADED
  if not LOADED:
    mod = vimspector.plugins
    # vimspector.plugins is a namespace package
    # Following:
    # https://packaging.python.org/guides/creating-and-discovering-plugins/#using-namespace-packages
    for finder, name, ispkg in pkgutil.iter_modules( mod.__path__,
                                                     mod.__name__ + '.' ):
      importlib.import_module( name )
    LOADED = 1

  return GADGETS



