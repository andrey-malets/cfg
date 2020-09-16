class ups {
    package { 'apcupsd':
        ensure => installed,
    }

    service { 'apcupsd':
        ensure => 'running',
        require => Package['apcupsd'],
    }

    file { '/etc/apcupsd/apcupsd.conf':
        notify  => Service['apcupsd'],
        mode    => '644',
        owner   => root,
        group   => root,
        content => template('ups/apcupsd.conf.erb'),
        require => Package['apcupsd'],
    }

    file { '/etc/default/apcupsd':
        notify  => Service['apcupsd'],
        mode  => '644',
        owner => root,
        group => root,
        content => "APCACCESS=/sbin/apcaccess
                    ISCONFIGURED=yes
                   ",
    }
}
