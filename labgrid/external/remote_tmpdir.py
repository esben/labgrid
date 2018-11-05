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
