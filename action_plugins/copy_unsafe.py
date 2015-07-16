# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os

from ansible import utils
import ansible.constants as C
import ansible.utils.template as template
from ansible import errors
from ansible.runner.return_data import ReturnData
import base64
import json
import stat
import tempfile
import pipes

## fixes https://github.com/ansible/ansible/issues/3518
# http://mypy.pythonblogs.com/12_mypy/archive/1253_workaround_for_python_bug_ascii_codec_cant_encode_character_uxa0_in_position_111_ordinal_not_in_range128.html
import sys
reload(sys)
sys.setdefaultencoding("utf8")


class ActionModule(object):

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp_path, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for file transfer operations '''

        # load up options
        options = {}
        if complex_args:
            options.update(complex_args)
        options.update(utils.parse_kv(module_args))
        source  = options.get('src', None)
        content = options.get('content', None)
        dest    = options.get('dest', None)

        # content with newlines is going to be escaped to safely load in yaml
        # now we need to unescape it so that the newlines are evaluated properly
        # when writing the file to disk
        if content:
            if isinstance(content, unicode):
                try:
                    content = content.decode('unicode-escape')
                except UnicodeDecodeError:
                    pass

        if (source is None and content is None and not 'first_available_file' in inject) or dest is None:
            result=dict(failed=True, msg="src (or content) and dest are required")
            return ReturnData(conn=conn, result=result)
        elif (source is not None or 'first_available_file' in inject) and content is not None:
            result=dict(failed=True, msg="src and content are mutually exclusive")
            return ReturnData(conn=conn, result=result)

        # Check if the source ends with a "/"
        source_trailing_slash = False
        if source:
            source_trailing_slash = source.endswith("/")

        # Define content_tempfile in case we set it after finding content populated.
        content_tempfile = None

        # If content is defined make a temp file and write the content into it.
        if content is not None:
            try:
                # If content comes to us as a dict it should be decoded json.
                # We need to encode it back into a string to write it out.
                if type(content) is dict:
                    content_tempfile = self._create_content_tempfile(json.dumps(content))
                else:
                    content_tempfile = self._create_content_tempfile(content)
                source = content_tempfile
            except Exception, err:
                result = dict(failed=True, msg="could not write content temp file: %s" % err)
                return ReturnData(conn=conn, result=result)
        # if we have first_available_file in our vars
        # look up the files and use the first one we find as src
        elif 'first_available_file' in inject:
            found = False
            for fn in inject.get('first_available_file'):
                fn_orig = fn
                fnt = template.template(self.runner.basedir, fn, inject)
                fnd = utils.path_dwim(self.runner.basedir, fnt)
                if not os.path.exists(fnd) and '_original_file' in inject:
                    fnd = utils.path_dwim_relative(inject['_original_file'], 'files', fnt, self.runner.basedir, check=False)
                if os.path.exists(fnd):
                    source = fnd
                    found = True
                    break
            if not found:
                results = dict(failed=True, msg="could not find src in first_available_file list")
                return ReturnData(conn=conn, result=results)
        else:
            source = template.template(self.runner.basedir, source, inject)
            if '_original_file' in inject:
                source = utils.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
            else:
                source = utils.path_dwim(self.runner.basedir, source)

        # A list of source file tuples (full_path, relative_path) which will try to copy to the destination
        source_files = []

        # If source is a directory populate our list else source is a file and translate it to a tuple.
        if os.path.isdir(source):
            # Get the amount of spaces to remove to get the relative path.
            if source_trailing_slash:
                sz = len(source) + 1
            else:
                sz = len(source.rsplit('/', 1)[0]) + 1

            # Walk the directory and append the file tuples to source_files.
            for base_path, sub_folders, files in os.walk(source):
                for file in files:
                    full_path = os.path.join(base_path, file)
                    rel_path = full_path[sz:]
                    source_files.append((full_path, rel_path))

            # If it's recursive copy, destination is always a dir,
            # explicitly mark it so (note - copy module relies on this).
            if not conn.shell.path_has_trailing_slash(dest):
                dest = conn.shell.join_path(dest, '')
        else:
            source_files.append((source, os.path.basename(source)))

        changed = False
        # expand any user home dir specifier
        dest = self.runner._remote_expand_user(conn, dest, tmp_path)

        for source_full, source_rel in source_files:
            # Generate a hash of the local file.
            local_checksum = utils.checksum(source_full)

            # This is kind of optimization - if user told us destination is
            # dir, do path manipulation right away, otherwise we still check
            # for dest being a dir via remote call below.
            if conn.shell.path_has_trailing_slash(dest):
                dest_file = conn.shell.join_path(dest, source_rel)
            else:
                dest_file = conn.shell.join_path(dest)

            conn.put_file(source_full, dest_file)
            changed = True


        if len(source_files) == 1:
            result =  {"changed": changed}
        else:
            result = dict(dest=dest, src=source, changed=changed)

        return ReturnData(conn=conn, result=result)

    def _create_content_tempfile(self, content):
        ''' Create a tempfile containing defined content '''
        fd, content_tempfile = tempfile.mkstemp()
        f = os.fdopen(fd, 'w')
        try:
            f.write(content)
        except Exception, err:
            os.remove(content_tempfile)
            raise Exception(err)
        finally:
            f.close()
        return content_tempfile
