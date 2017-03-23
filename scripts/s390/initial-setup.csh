# initial-setup.csh

set IS_EXEC = /usr/libexec/initial-setup/run-initial-setup
set IS_UNIT = initial-setup.service

# the initial-setup-text.service is deprecated, use initial-setup.service instead
set IS_UNIT_TEXT = initial-setup-text.service

# the initial-setup-graphical.service is deprecated, use initial-setup.service instead
set IS_UNIT_GRAPHICAL = initial-setup-graphical.service

# check if the Initial Setup unit is enabled and the executable is available
# - either the initial-setup.service or initial-setup-text.service need to be enabled
if ( ( { systemctl -q is-enabled $IS_UNIT } || { systemctl -q is-enabled $IS_UNIT_TEXT } || { systemctl -q is-enabled $IS_UNIT_GRAPHICAL } ) && -x $IS_EXEC ) then
    # check if we're not on 3270 terminal and root
    if (( `/sbin/consoletype` == "pty" ) && ( `/usr/bin/id -u` == 0 )) then
        $IS_EXEC
    endif
endif
