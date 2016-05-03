# firstboot.sh

IS_EXEC=/lib/exec/initial-setup-text
IS_UNIT=initial-setup.service

IS_AVAILABLE=0
# check if the Initial Setup unit is enabled and the executable is available
systemctl -q is-enabled $IS_UNIT && [ -f $IS_EXEC ] && IS_AVAILABLE=1
if [ $IS_AVAILABLE -eq 1 ]; then
    # check if we're not on 3270 terminal and root
    if [ $(/sbin/consoletype) = "pty" ] && [ $EUID -eq 0 ]; then
        $IS_EXEC && systemctl -q is-enabled $IS_UNIT && systemctl -q disable $IS_UNIT
    fi
fi
