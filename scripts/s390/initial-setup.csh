# initial-setup.csh

set IS_EXEC = /usr/libexec/initial-setup/initial-setup-text
set IS_UNIT = initial-setup.service

# check if the Initial Setup unit is enabled and the executable is available
if ( { systemctl -q is-enabled $IS_UNIT } && -x $IS_EXEC ) then
    # check if we're not on 3270 terminal and root
    if (( `/sbin/consoletype` == "pty" ) && ( `/usr/bin/id -u` == 0 )) then
        $IS_EXEC --no-stdout-log --no-multi-tty && systemctl -q is-enabled $IS_UNIT && systemctl -q disable $IS_UNIT && systemctl -q stop $IS_UNIT
    endif
endif
