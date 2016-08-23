# initial-setup.sh

IS_EXEC=/usr/libexec/initial-setup/initial-setup-text
IS_UNIT=initial-setup.service

# the initial-setup-text.service is deprecated, use initial-setup.service instead
IS_UNIT_TEXT=initial-setup.service

IS_AVAILABLE=0
# check if the Initial Setup unit is enabled and the executable is available
# - either the initial-setup.service or initial-setup-text.service need to be enabled
systemctl -q is-enabled $IS_UNIT || systemctl -q is-enabled $IS_UNIT_TEXT && [ -f $IS_EXEC ] && IS_AVAILABLE=1
if [ $IS_AVAILABLE -eq 1 ]; then
    # check if we're not on 3270 terminal and root
    if [ $(/sbin/consoletype) = "pty" ] && [ $EUID -eq 0 ]; then
        $IS_EXEC --no-stdout-log
        if [ $? == 0 ]; then
            # everything apparently went well, disable all relevant Initial Setup units
            systemctl -q is-enabled $IS_UNIT && systemctl -q disable $IS_UNIT
            systemctl -q is-enabled $IS_UNIT_TEXT && systemctl -q disable $IS_UNIT_TEXT
        fi
    fi
fi
