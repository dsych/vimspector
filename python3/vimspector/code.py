# vimspector - A multi-language debugging system for Vim
# Copyright 2018 Ben Jackson
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

import vim
import logging
import json
from collections import defaultdict

from vimspector import utils, terminal, signs


class CodeView( object ):
  def __init__( self, window, api_prefix ):
    self._window = window
    self._api_prefix = api_prefix

    self._terminal = None
    self.current_syntax = None

    self._logger = logging.getLogger( __name__ )
    utils.SetUpLogging( self._logger )

    # FIXME: This ID is by group, so should be module scope
    self._next_sign_id = 1
    self._signs = {
      'vimspectorPC': None,
    }
    self._current_frame = None

    with utils.LetCurrentWindow( self._window ):
      if utils.UseWinBar():
        # Buggy neovim doesn't render correctly when the WinBar is defined:
        # https://github.com/neovim/neovim/issues/12689
        vim.command( 'nnoremenu WinBar.■\\ Stop '
                     ':call vimspector#Stop()<CR>' )
        vim.command( 'nnoremenu WinBar.▶\\ Cont '
                     ':call vimspector#Continue()<CR>' )
        vim.command( 'nnoremenu WinBar.▷\\ Pause '
                     ':call vimspector#Pause()<CR>' )
        vim.command( 'nnoremenu WinBar.↷\\ Next '
                     ':call vimspector#StepOver()<CR>' )
        vim.command( 'nnoremenu WinBar.→\\ Step '
                     ':call vimspector#StepInto()<CR>' )
        vim.command( 'nnoremenu WinBar.←\\ Out '
                     ':call vimspector#StepOut()<CR>' )
        vim.command( 'nnoremenu WinBar.⟲: '
                     ':call vimspector#Restart()<CR>' )
        vim.command( 'nnoremenu WinBar.✕ '
                     ':call vimspector#Reset()<CR>' )

      if not signs.SignDefined( 'vimspectorPC' ):
        signs.DefineSign( 'vimspectorPC',
                          text = '▶',
                          double_text = '▶',
                          texthl = 'MatchParen',
                          linehl = 'CursorLine' )
      if not signs.SignDefined( 'vimspectorPCBP' ):
        signs.DefineSign( 'vimspectorPCBP',
                          text = '●▶',
                          double_text  = '▷',
                          texthl = 'MatchParen',
                          linehl = 'CursorLine' )


  def _UndisplayPC( self, clear_pc = True ):
    if clear_pc:
      self._current_frame = None
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None


  def SetCurrentFrame( self, frame ):
    """Returns True if the code window was updated with the frame, False
    otherwise. False means either the frame is junk, we couldn't find the file
    (or don't have the data) or the code window no longer exits."""

    if not frame or not frame.get( 'source' ):
      self._UndisplayPC()
      return False

    if 'path' not in frame[ 'source' ]:
      self._UndisplayPC()
      return False

    self._current_frame = frame

    if not self._window.valid:
      return False

    utils.JumpToWindow( self._window )
    try:
      utils.OpenFileInCurrentWindow( frame[ 'source' ][ 'path' ] )
      vim.command( 'doautocmd <nomodeline> User VimspectorJumpedToFrame' )
    except vim.error:
      self._logger.exception( 'Unexpected vim error opening file {}'.format(
        frame[ 'source' ][ 'path' ] ) )
      return False

    # SIC: column is 0-based, line is 1-based in vim. Why? Nobody knows.
    # Note: max() with 0 because some debug adapters (go) return 0 for the
    # column.
    try:
      self._window.cursor = ( frame[ 'line' ], max( frame[ 'column' ] - 1, 0 ) )
    except vim.error:
      self._logger.exception( "Unable to jump to %s:%s in %s, maybe the file "
                              "doesn't exist",
                              frame[ 'line' ],
                              frame[ 'column' ],
                              frame[ 'source' ][ 'path' ] )
      return False

    self.current_syntax = utils.ToUnicode(
      vim.current.buffer.options[ 'syntax' ] )

    return True

  def Clear( self ):
    if self._signs[ 'vimspectorPC' ]:
      signs.UnplaceSign( self._signs[ 'vimspectorPC' ], 'VimspectorCode' )
      self._signs[ 'vimspectorPC' ] = None

    self._UndisplayPC()
    self.current_syntax = None

  def Reset( self ):
    self.Clear()

  def Refresh( self, file_name ):
    return


  def LaunchTerminal( self, params ):
    self._terminal = terminal.LaunchTerminal( self._api_prefix,
                                              params,
                                              window_for_start = self._window,
                                              existing_term = self._terminal )

    # FIXME: Change this tor return the PID rather than having debug_session
    # work that out
    return self._terminal.buffer_number
