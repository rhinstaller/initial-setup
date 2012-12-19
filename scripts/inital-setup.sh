# firstboot.sh

FIRSTBOOT_EXEC=/usr/sbin/firstboot
FIRSTBOOT_CONF=/etc/sysconfig/firstboot

# source the config file
[ -f $FIRSTBOOT_CONF ] && . $FIRSTBOOT_CONF

# check if we should run firstboot
if [ -f $FIRSTBOOT_EXEC ] && [ "${RUN_FIRSTBOOT,,}" = "yes" ]; then
    # check if we're not on 3270 terminal and root
    if [ $(/sbin/consoletype) = "pty" ] && [ $EUID -eq 0 ]; then
        args=""
        if grep -i "reconfig" /proc/cmdline >/dev/null || [ -f /etc/reconfigSys ]; then
            args="--reconfig"
        fi

        . /etc/sysconfig/i18n
        $FIRSTBOOT_EXEC $args
    fi
fi
