# initial-setup.csh

set IS_EXEC = /lib/exec/initial-setup-text
set IS_UNIT = initial-setup.service

# the initial-setup-text.service is depreciated, use initial-setup.service instead
set IS_UNIT_TEXT = initial-setup-text.service

# check if the Initial Setup unit is enabled and the executable is available
# - either the initial-setup.service or initial-setup-text.service need to be enabled
if ( ( { systemctl -q is-enabled $IS_UNIT } || { systemctl -q is-enabled $IS_UNIT_TEXT } ) && -x $IS_EXEC ) then
    # check if we're not on 3270 terminal and root
    if (( `/sbin/consoletype` == "pty" ) && ( `/usr/bin/id -u` == 0 )) then
        $IS_EXEC
        if ( $? == 0 ) then
            # everything apparently went well, disable all relevant Initial Setup units
            systemctl -q is-enabled $IS_UNIT && systemctl -q disable $IS_UNIT
            systemctl -q is-enabled $IS_UNIT_TEXT && systemctl -q disable $IS_UNIT_TEXT
        endif
    endif
endif
