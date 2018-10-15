import os
import os.path


class RemoteTmpdir:
    """ RemoteTmpdir - A class that maintains a temporary directory on a remote
    linux system.
    E.g. when copying a test script or binary to DUT, RemoteTmpdir assists to
    prevent pollution of the target.

    RemoteTmpdir is to be created in a fixture, which can take care of a
    test module in a subdirectory. Recommended scope is function to avoid
    polution between tests.

    See examples/remote_tmpdir.

    Arguments:
        shell: Driver instance implementing CommandProtocol
        basedir: directory relative to pytest root
        filetransfer: Driver instance implementing FileTransferProtocol
            (defaults to shell)
    """
    def __init__(self, shell, basedir=None, filetransfer=None):
        stdout = shell.run_check('mktemp -d')
        self.path = stdout[0] + '/'
        if filetransfer is None:
            filetransfer = shell
        self.filetransfer = filetransfer
        self.shell = shell
        self.basedir = basedir

        if self.basedir is not None and not os.path.isdir(self.basedir):
            raise Exception('RemoteTmpdir: {} is not a directory'.format(
                self.basedir))

    def put(self, *items):
        """Copy a file or contents of directory to the created tmpdir.

        Arguments:
            *items: list of files or directories to copy (does not create sub
                directories, but copies all files)
        """
        for path in items:
            # resolve relative paths
            if not os.path.isabs(path) and self.basedir is not None:
                path = os.path.join(self.basedir, path)

            if os.path.isfile(path):
                remotepath = self.path + os.path.basename(path)
                self.filetransfer.put(path, remotepath)
            else:
                # then it is a whole directory to copy
                for filename in os.listdir(path):
                    localpath = os.path.join(path, filename)
                    remotepath = self.path + filename
                    if os.path.isfile(localpath):
                        self.filetransfer.put(localpath, remotepath)

    def get(self, *files, localdir=None):
        """Download files from the remote tmpdir.

        Arguments:
            *files: list of files to download
            localdir: directory to download files to
        """
        for path in files:
            remotepath = self.path + str(path)
            assert localdir or self.basedir, 'RemoteTmpdir does not have basedir set, use localdir= in get'
            self.filetransfer.get(remotepath, localdir or self.basedir)

    def cleanup(self):
        """Remove the directory again on target."""
        # usual teardown code, thus failure ignored but returned
        try:
            self.shell.run_check('rm -r {}'.format(self.path))
            return True
        except Exception:
            return False

    def run_check(self, cmd, *args, **kwargs):
        """Upload and execute file.

        Convenience function for uploading executable file and then executing
        command using run_check() method of the shell of RemoteTmpdir object.

        Example:

            tmpdir.run_check('/local/script --foobar')

        to upload /local/script to remote tmpdir, and then execute it from
        there with '--foobar' argument.

        Arguments:
            cmd: command to execute, with command specified locally
            *args: positional arguments to CommandProtcol.run_check()
            **kwargs: keyword arguments to CommandProtcol.run_check()

        """
        cmdv = cmd.split(maxsplit=1)
        localpath = cmdv[0]
        filename = os.path.basename(localpath)
        remotepath = self.path + filename
        cmdv[0] = remotepath
        self.put(localpath)
        return self.shell.run_check(' '.join(cmdv), *args, **kwargs)
