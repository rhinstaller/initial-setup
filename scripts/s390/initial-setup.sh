# initial-setup.sh

IS_EXEC=/usr/libexec/initial-setup/run-initial-setup
IS_UNIT=initial-setup.service

# the initial-setup-text.service is deprecated, use initial-setup.service instead
IS_UNIT_TEXT=initial-setup-text.service
# the initial-setup-graphical.service is deprecated, use initial-setup.service instead
IS_UNIT_GRAPHICAL=initial-setup-graphical.service

IS_AVAILABLE=0
# check if the Initial Setup unit is enabled and the executable is available
# - either of the initial-setup.service, initial-setup-text.service or initial-setup graphical
# need to be enabled
UNIT_ENABLED=0
systemctl -q is-enabled $IS_UNIT || systemctl -q is-enabled $IS_UNIT_TEXT || systemctl -q is-enabled $IS_UNIT_GRAPHICAL && UNIT_ENABLED=1
[ $UNIT_ENABLED -eq 1 ] && [ -f $IS_EXEC ] && IS_AVAILABLE=1
if [ $IS_AVAILABLE -eq 1 ]; then
    # check if we're not on 3270 terminal and root
    if [ $(/sbin/consoletype) = "pty" ] && [ $EUID -eq 0 ]; then
        $IS_EXEC
    fi
fi
