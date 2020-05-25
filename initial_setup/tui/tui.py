from pyanaconda.ui.tui import TextUserInterface
from pyanaconda import threading

from initial_setup.product import product_title, is_final
from initial_setup.common import list_usable_consoles_for_tui, get_quit_message
from initial_setup.i18n import _, N_
from .hubs import InitialSetupMainHub

from simpleline import App

import os
import sys
import select
import contextlib
import termios
import logging
log = logging.getLogger("initial-setup")

QUIT_MESSAGE = get_quit_message()

class MultipleTTYHandler(object):
    """Run the Initial Setup TUI on all usable consoles.

    This is done by redirecting the Initial Setup stdout to all
    usable consoles and then redirecting any input back to
    the Initial Setup stdin.
    """

    def __init__(self, tui_stdout_fd, tui_stdin_fd):
        # create file objects for the TUI stdout and stdin fds
        self._tui_stdout_fd = tui_stdout_fd
        self._tui_stdout = os.fdopen(tui_stdout_fd, "r")
        self._tui_stdin_fd = tui_stdin_fd
        self._tui_stdin = os.fdopen(tui_stdin_fd, "w")

        self._shutdown = False

        self._active_console = None

        self._console_read_fos = {}
        self._console_write_fos = []
        self._open_all_consoles()

    def shutdown(self):
        """Tell the multi TTY handler to shutdown."""
        self._shutdown = True

    def _open_all_consoles(self):
        """Open all consoles suitable for running the Initial Setup TUI."""
        console_write_fos = {}
        console_read_fos = {}
        console_paths = (os.path.join("/dev", c) for c in list_usable_consoles_for_tui())
        usable_console_paths = []
        unusable_console_paths = []
        for console_path in console_paths:
            try:
                write_fo = open(console_path, "w")
                read_fo = open(console_path, "r")
                fd = read_fo.fileno()
                console_write_fos[fd] = write_fo
                # the console stdin file descriptors need to be non-blocking
                os.set_blocking(fd, False)
                console_read_fos[fd] = read_fo
                # If we survived till now the console might be usable
                # (could be read and written into).
                usable_console_paths.append(console_path)
            except Exception:
                log.exception("can't open console for Initial Setup TUI: %s", console_path)
                unusable_console_paths.append(console_path)

        log.debug("The Initial Setup TUI will attempt to run on the following consoles:")
        log.debug("\n".join(usable_console_paths))
        log.debug("The following consoles could not be opened and will not be used:")
        log.debug("\n".join(unusable_console_paths))
        self._console_read_fos = console_read_fos
        self._console_write_fos = console_write_fos

    def run(self):
        """Run IS TUI on multiple consoles."""
        # we wait for data from the consoles
        fds = list(self._console_read_fos.keys())
        # as well as from the anaconda stdout
        fds.append(self._tui_stdout_fd)
        log.info("multi TTY handler starting")
        while True:
            # Watch the consoles and IS TUI stdout for data and
            # react accordingly.
            # The select also triggers every second (the 1.0 parameter),
            # so that the infinite loop can be promptly interrupted once
            # the multi TTY handler is told to shutdown.
            rlist, _wlist, _xlist = select.select(fds, [], [], 1.0)
            if self._shutdown:
                log.info("multi TTY handler shutting down")
                break
            for fd in rlist:
                if fd == self._tui_stdout_fd:
                    # We need to set the TUI stdout fd to non-blocking,
                    # as otherwise reading from it would (predictably) result in
                    # the readline() function blocking once it runs out of data.
                    os.set_blocking(fd, False)

                    # The IS TUI wants to write something,
                    # read all the lines.
                    lines = self._tui_stdout.readlines()

                    # After we finish reading all the data we need to set
                    # the TUI stdout fd to blocking again.
                    # Otherwise the fd will not be usable when we try to read from
                    # it again for unclear reasons.
                    os.set_blocking(fd, True)

                    lines.append("\n")  # seems to get lost somewhere on the way

                    # Write all the lines IS wrote to stdout to all consoles
                    # that we consider usable for the IS TUI.
                    for console_fo in self._console_write_fos.values():
                        for one_line in lines:
                            try:
                                console_fo.write(one_line)
                            except OSError:
                                log.exception("failed to write %s to console %s", one_line, console_fo)
                else:
                    # Someone typed some input to a console and hit enter,
                    # forward the input to the IS TUI stdin.
                    read_fo = self._console_read_fos[fd]
                    write_fo = self._console_write_fos[fd]
                    # as the console is getting input we consider it to be
                    # the currently active console
                    self._active_console = read_fo, write_fo
                    try:
                        data = read_fo.readline()
                    except TypeError:
                        log.exception("input reading failed for console %s", read_fo)
                        continue
                    self._tui_stdin.write(data)
                    self._tui_stdin.flush()

    def custom_getpass(self, prompt='Password: '):
        """Prompt for a password, with echo turned off that can run on an arbitrary console.

        This implementation is based on the Python 3.6 getpass() source code, with added
        support for running getpass() on an arbitrary console, as the original implementation
        is hardcoded to expect input from /dev/tty, without an option to change that.

        Raises:
          EOFError: If our input tty or stdin was closed.

        Always restores terminal settings before returning.
        """
        input_fo, output_fo = self._active_console
        passwd = None
        with contextlib.ExitStack() as stack:
            input_fd = input_fo.fileno()
            if input_fd is not None:
                try:
                    old = termios.tcgetattr(input_fd)     # a copy to save
                    new = old[:]
                    new[3] &= ~termios.ECHO  # 3 == 'lflags'
                    tcsetattr_flags = termios.TCSAFLUSH
                    if hasattr(termios, 'TCSASOFT'):
                        tcsetattr_flags |= termios.TCSASOFT
                    try:
                        termios.tcsetattr(input_fd, tcsetattr_flags, new)
                        passwd = self._raw_input(prompt, output_fo, input_fo=input_fo)
                    finally:
                        termios.tcsetattr(input_fd, tcsetattr_flags, old)
                        output_fo.flush()  # Python issue7208
                except termios.error:
                    if passwd is not None:
                        # _raw_input succeeded.  The final tcsetattr failed.  Reraise
                        # instead of leaving the terminal in an unknown state.
                        raise
                    # We can't control the tty or stdin.  Give up and use normal IO.
                    # _fallback_getpass() raises an appropriate warning.
                    if output_fo is not input_fo:
                        # clean up unused file objects before blocking
                        stack.close()
                    passwd = self._fallback_getpass(prompt, output_fo, input_fo)

            output_fo.write('\n')
            return passwd

    def _fallback_getpass(self, prompt='Password: ', output_fo=None, input_fo=None):
        log.warning("Can not control echo on the terminal: %s", input_fo)
        if not output_fo:
            output_fo = sys.stderr
        print("Warning: Password input may be echoed.", file=output_fo)
        return self._raw_input(prompt, output_fo, input_fo)


    def _raw_input(self, prompt="", output_fo=None, input_fo=None):
        # This doesn't save the string in the GNU readline history.

        # The input fd has to be set as non-blocking for the general multi-tty machinery
        # to work, but for password input to work correctly it needs to be set as blocking
        # when user input is expected.
        # We also have to switch it back to non-blocking once user input is received.
        os.set_blocking(input_fo.fileno(), True)
        prompt = str(prompt)
        if prompt:
            try:
                output_fo.write(prompt)
            except UnicodeEncodeError:
                # Use replace error handler to get as much as possible printed.
                prompt = prompt.encode(output_fo.encoding, 'replace')
                prompt = prompt.decode(output_fo.encoding)
                output_fo.write(prompt)
            output_fo.flush()
        # NOTE: The Python C API calls flockfile() (and unlock) during readline.
        line = input_fo.readline()
        if not line:
            raise EOFError
        if line[-1] == '\n':
            line = line[:-1]
        # We got input from the user, switch the input fd back to non-blocking
        # so that the multi-tty machinery works correctly.
        os.set_blocking(input_fo.fileno(), False)
        return line


class InitialSetupTextUserInterface(TextUserInterface):
    """This is the main text based firstboot interface. It inherits from
       anaconda to make the look & feel as similar as possible.
    """

    ENVIRONMENT = "firstboot"

    def __init__(self):
        TextUserInterface.__init__(self, None, None, product_title, is_final,
                                   quitMessage=QUIT_MESSAGE)

        # redirect stdin and stdout to custom pipes

        # stdin
        stdin_fd, tui_stdin_fd = os.pipe()
        sys.stdin = os.fdopen(stdin_fd, "r")

        # stdout
        tui_stdout_fd, stdout_fd = os.pipe()
        sys.stdout = os.fdopen(stdout_fd, "w")

        # instantiate and start the multi TTY handler
        self.multi_tty_handler = MultipleTTYHandler(tui_stdin_fd=tui_stdin_fd, tui_stdout_fd=tui_stdout_fd)
        # start the multi-tty handler
        threading.threadMgr.add(
            threading.AnacondaThread(name="initial_setup_multi_tty_thread", target=self.multi_tty_handler.run)
        )

    def setup(self, data):
        TextUserInterface.setup(self, data)
        # Make sure custom getpass() from multi-tty handler is used instead of regular getpass.
        # This needs to be done as the default getpass() implementation cant work with arbitrary
        # consoles and always defaults to /dev/tty for input.
        configuration = App.get_configuration()
        configuration.password_function = self.multi_tty_handler.custom_getpass

    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "firstboot.tui"
    basepath = os.path.dirname(__file__)
    paths = TextUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }

