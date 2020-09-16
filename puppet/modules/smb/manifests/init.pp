class smb inherits place {
    package { 'samba': ensure => installed }

    file { '/etc/smb.pwd':
        ensure => present,
        mode => '400',
        owner => root,
        group => root,
        source => 'puppet:///files/smb.pwd',
    }

    file { '/etc/samba/smb.conf':
        ensure => present,
        mode => '644',
        owner => root,
        group => root,
        content => template('smb/smb.conf.erb'),
    }

    exec { 'join':
        command => '/usr/bin/net ads join -U unix_manager < /etc/smb.pwd',
        require => [File['/etc/smb.pwd'],
                    File['/etc/samba/smb.conf']],
        subscribe => [File['/etc/smb.pwd'],
                      File['/etc/samba/smb.conf']],
        refreshonly => true,
    }

    service { 'smbd':
        ensure => running,
        enable => true,
        require => [File['/etc/smb.pwd'],
                    File['/etc/samba/smb.conf']],
        subscribe => [File['/etc/smb.pwd'],
                      File['/etc/samba/smb.conf'],
                      Exec['join']],
    }

    service { 'nmbd':
        ensure => running,
        enable => true,
        require => [File['/etc/smb.pwd'],
                    File['/etc/samba/smb.conf']],
        subscribe => [File['/etc/smb.pwd'],
                      File['/etc/samba/smb.conf'],
                      Exec['join']],
    }
}
