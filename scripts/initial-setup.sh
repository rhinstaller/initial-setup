# initial-setup.sh

IS_EXEC=/usr/bin/initial-setup
IS_CONF=/etc/sysconfig/initial-setup

# source the config file
[ -f $IS_CONF ] && . $IS_CONF

# check if we should run initial-setup
if [ -f $IS_EXEC ] && [ "${RUN_INITIAL_SETUP,,}" = "yes" ]; then
    # check if we're not on 3270 terminal and root
    if [ $(/sbin/consoletype) = "pty" ] && [ $EUID -eq 0 ]; then
        args=""
        if grep -i "reconfig" /proc/cmdline >/dev/null || [ -f /etc/reconfigSys ]; then
            args="--reconfig"
        fi

        . /etc/locale.conf
        . /etc/vconsole.conf
        $IS_EXEC $args
        [ $? -eq 0 ] && sed -r -i 's/^RUN_INITIAL_SETUP\s*=\s*[yY][eE][sS]\s*/RUN_INITIAL_SETUP=NO/' $IS_CONF
    fi
fi
