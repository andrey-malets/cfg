class cron-apt {
    package { 'cron-apt': ensure => installed }

    file { '/etc/cron-apt/config':
        mode => 644,
        owner => root,
        group => root,
        content => template('cron-apt/config.erb'),
    }
}
