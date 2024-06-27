from Testing import get_tested_mock_package


SYSVINITONSYSTEMD = get_tested_mock_package(
files={
'/etc/init.d/boot.script': {'content': ''},
'/etc/init.d/weekly.script': {'content': ''}
},
header={
'requires': ['insserv']
})


SYSVINITONSYSTEMD2 = get_tested_mock_package(
files={
'/etc/init.d/bar': {'content': """
#! /bin/bash

### BEGIN INIT INFO
# Provides:          foo
# Required-Start:    $local_fs $network
# Required-Stop:     $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: foo service
# Description:       Run Foo service
### END INIT INFO

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting Foo..."
    sudo -u foo-user bash -c 'cd /path/to/scripts/ && ./start-foo.sh'
    ;;
  stop)
    echo "Stopping Foo..."
    sudo -u foo-user bash -c 'cd /path/to/scripts/ && ./stop-foo.sh'
    sleep 2
    ;;
  *)
    echo "Usage: /etc/init.d/foo {start|stop}"
    exit 1
    ;;
esac

exit 0
"""},
'/usr/lib/systemd/system/bar.service': {},
'/usr/lib/systemd/system/foo.service': {}},
header={
'requires': ['insserv']})
