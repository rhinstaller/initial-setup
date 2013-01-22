# initial-setup.csh

set IS_EXEC = /usr/sbin/initial-setup
set IS_CONF = /etc/sysconfig/initial-setup

# check if we should run firstboot
grep -i "RUN_INITIAL_SETUP=NO" $IS_CONF >/dev/null
if (( $? != 0 ) && ( -x $IS_EXEC )) then
    # check if we're not on 3270 terminal and root
    if (( `/sbin/consoletype` == "pty" ) && ( `/usr/bin/id -u` == 0 )) then
        set args = ""
        grep -i "reconfig" /proc/cmdline >/dev/null
        if (( $? == 0 ) || ( -e /etc/reconfigSys )) then
            set args = "--reconfig"
        endif

        $IS_EXEC $args
    endif
endif
