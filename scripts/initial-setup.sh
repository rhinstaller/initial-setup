# firstboot.sh

IS_EXEC=/usr/sbin/initial-setup
IS_CONF=/etc/sysconfig/initial-setup

# source the config file
[ -f $IS_CONF ] && . $IS_CONF

# check if we should run firstboot
if [ -f $IS_EXEC ] && [ "${RUN_INITIAL_SETUP,,}" = "yes" ]; then
    # check if we're not on 3270 terminal and root
    if [ $(/sbin/consoletype) = "pty" ] && [ $EUID -eq 0 ]; then
        args=""
        if grep -i "reconfig" /proc/cmdline >/dev/null || [ -f /etc/reconfigSys ]; then
            args="--reconfig"
        fi

        . /etc/sysconfig/i18n
        $IS_EXEC $args
    fi
fi
