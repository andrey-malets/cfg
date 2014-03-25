class nrpe {
    package { 'nagios-nrpe-server':
        ensure => installed,
        install_options => norecommended,
    }

    package { 'nagios-plugins-basic':
        ensure => installed,
        install_options => norecommended,
    }

    service { 'nagios-nrpe-server':
        ensure     => 'running',
        enable     => 'true',
        hasrestart => 'true',
        hasstatus  => 'false',
        restart    => '/etc/init.d/nagios-nrpe-server restart',
        pattern    => '/usr/sbin/nrpe',
        require => [Package['nagios-nrpe-server'],
                    Package['nagios-plugins-basic'],
                    File['/etc/nagios/nrpe.cfg']],
    }

    file { '/etc/nagios/nrpe.cfg':
        notify => Service['nagios-nrpe-server'],
        mode => 644,
        owner => root,
        group => root,
        content => template('nrpe/nrpe.cfg.erb'),
        require => [Package['nagios-nrpe-server'],
                    Package['nagios-plugins-basic']],
    }

    if $check_hadoop_slave or $check_hadoop_master {
        file { '/usr/lib/nagios/plugins/check_hadoop':
            mode => 755,
            owner => root,
            group => root,
            source => "puppet:///files/check_hadoop",
        }

        file { '/etc/sudoers.d/nagios-jps':
            content => 'nagios ALL=(ALL) NOPASSWD: /usr/lib/nagios/plugins/check_hadoop *
',
            mode => 440,
            owner => root,
            group => root,
        }
    }
}
