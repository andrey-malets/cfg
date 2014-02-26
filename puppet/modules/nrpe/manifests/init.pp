class nrpe {
    service { 'nagios-nrpe-server':
        ensure     => 'running',
        enable     => 'true',
        hasrestart => 'true',
        hasstatus  => 'false',
        restart    => '/etc/init.d/nagios-nrpe-server restart',
        pattern    => '/usr/sbin/nrpe',
    }

    file { '/etc/nagios/nrpe.cfg':
        notify => Service['nagios-nrpe-server'],
        mode => 644,
        owner => root,
        group => root,
        content => template('nrpe/nrpe.cfg.erb')
    }
}
