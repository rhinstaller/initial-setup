from pyanaconda.ui.tui import TextUserInterface
from pyanaconda import threads
from initial_setup.product import product_title, is_final
from initial_setup.common import list_usable_consoles_for_tui
from .hubs import InitialSetupMainHub
import os
import sys
import gettext
import select
import logging
log = logging.getLogger("initial-setup")

# localization
_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

QUIT_MESSAGE = N_("Are you sure you want to quit the configuration process?\n"
                  "You might end up with unusable system if you do.")

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

        self._console_read_fds = {}
        self._console_write_fos = []
        self._open_all_consoles()

    def shutdown(self):
        """Tell the multi TTY handler to shutdown."""
        self._shutdown = True

    def _open_all_consoles(self):
        """Open all consoles suitable for running the Initial Setup TUI."""
        console_write_fos = []
        console_read_fds = {}
        console_paths = (os.path.join("/dev", c) for c in list_usable_consoles_for_tui())
        usable_console_paths = []
        unusable_console_paths = []
        for console_path in console_paths:
            try:
                write_fo = open(console_path, "w")
                read_fo = open(console_path, "r")
                console_write_fos.append(write_fo)
                read_fd = read_fo.fileno()
                # the console stdin file descriptors need to be non-blocking
                os.set_blocking(read_fd, False)
                console_read_fds[read_fd] = read_fo
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
        self._console_read_fds = console_read_fds
        self._console_write_fos = console_write_fos

    def run(self):
        """Run IS TUI on multiple consoles."""
        # we wait for data from the consoles
        fds = list(self._console_read_fds.keys())
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
                    for console_fo in self._console_write_fos:
                        for one_line in lines:
                            try:
                                console_fo.write(one_line)
                            except OSError:
                                log.exception("failed to write %s to console %s", one_line, console_fo)
                else:
                    # Someone typed some input to a console and hit enter,
                    # forward the input to the IS TUI stdin.
                    fo = self._console_read_fds[fd]
                    try:
                        data = fo.readline()
                    except TypeError:
                        log.exception("input reading failed for console %s", fo)
                        continue
                    self._tui_stdin.write(data)
                    self._tui_stdin.flush()


class InitialSetupTextUserInterface(TextUserInterface):
    """This is the main text based firstboot interface. It inherits from
       anaconda to make the look & feel as similar as possible.
    """

    ENVIRONMENT = "firstboot"

    def __init__(self, storage, payload, instclass):
        TextUserInterface.__init__(self, storage, payload, instclass,
                                   product_title, is_final, quitMessage=QUIT_MESSAGE)

        # redirect stdin and stdout to custom pipes

        # stdin
        stdin_fd, tui_stdin_fd = os.pipe()
        sys.stdin = os.fdopen(stdin_fd, "r")

        # stdout
        tui_stdout_fd, stdout_fd = os.pipe()
        sys.stdout = os.fdopen(stdout_fd, "w")

        # instantiate and start the multi TTY handler
        self.multi_tty_handler = MultipleTTYHandler(tui_stdin_fd=tui_stdin_fd, tui_stdout_fd=tui_stdout_fd)
        threads.threadMgr.add(
            threads.AnacondaThread(name="such_multi_tty_thread", target=self.multi_tty_handler.run)
        )

    def _list_hubs(self):
        return [InitialSetupMainHub]

    basemask = "firstboot.tui"
    basepath = os.path.dirname(__file__)
    paths = TextUserInterface.paths + {
        "spokes": [(basemask + ".spokes.%s", os.path.join(basepath, "spokes"))],
        "categories": [(basemask + ".categories.%s", os.path.join(basepath, "categories"))],
        }

