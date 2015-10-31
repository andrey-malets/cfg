class nrpe {
    package { 'nagios-nrpe-server':
        ensure => installed,
        install_options => '--no-install-recommends',
    }

    package { 'nagios-plugins-basic':
        ensure => installed,
        install_options => '--no-install-recommends',
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

    service { 'nagios-nrpe-server':
        ensure     => 'running',
        enable     => 'true',
        require => [Package['nagios-nrpe-server'],
                    Package['nagios-plugins-basic'],
                    File['/etc/nagios/nrpe.cfg']],
    }

    if $check_megaraid {
        file { '/etc/sudoers.d/nagios-megaraid':
            content => 'nagios ALL=(ALL) NOPASSWD: /usr/sbin/megacli *
',
            mode => 440,
            owner => root,
            group => root,
        }
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
