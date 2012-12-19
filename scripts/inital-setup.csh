# firstboot.csh

set FIRSTBOOT_EXEC = /usr/sbin/firstboot
set FIRSTBOOT_CONF = /etc/sysconfig/firstboot

# check if we should run firstboot
grep -i "RUN_FIRSTBOOT=NO" $FIRSTBOOT_CONF >/dev/null
if (( $? != 0 ) && ( -x $FIRSTBOOT_EXEC )) then
    # check if we're not on 3270 terminal and root
    if (( `/sbin/consoletype` == "pty" ) && ( `/usr/bin/id -u` == 0 )) then
        set args = ""
        grep -i "reconfig" /proc/cmdline >/dev/null
        if (( $? == 0 ) || ( -e /etc/reconfigSys )) then
            set args = "--reconfig"
        endif

        $FIRSTBOOT_EXEC $args
    endif
endif
