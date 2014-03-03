class cron-apt {
    package { 'cron-apt': ensure => installed }

    file { '/etc/cron-apt/config':
        mode => 644,
        owner => root,
        group => root,
        content => template('cron-apt/config.erb'),
        require => Package['cron-apt'],
    }

    if $autoupdate {
        file { '/etc/cron-apt/action.d/3-download':
            mode => 644,
            owner => root,
            group => root,
            source => 'puppet:///modules/cron-apt/3-download',
            require => Package['cron-apt'],
        }
    }
}
