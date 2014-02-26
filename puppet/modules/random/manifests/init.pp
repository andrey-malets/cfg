class random {
    package { 'nsca-client': ensure => installed }

    file { 'puppet.random.sh':
        path => '/usr/local/bin/puppet.random.sh',
        mode => 755,
        owner => root,
        group => root,
        content => template('random/puppet.random.sh.erb')
    }

    file { 'puppet.random':
        path => '/usr/local/puppet.random',
        ensure => present,
        mode => '644',
        owner => root,
        group => root,
        source => 'puppet:///files/random',
    }

    cron { 'puppet.random.sh':
        command => '/usr/local/bin/puppet.random.sh',
        user => root,
        hour => '*/3',
        minute => '0',
        require => [File['puppet.random'], File['puppet.random.sh']],
    }
}
