class smb inherits place {
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

#    file { '/usr/local/bin/join.sh':
#        ensure => present,
#        mode => '700',
#        owner => root,
#        group => root,
#        source => 'puppet:///files/join.sh',
#    }

#    exec { '/usr/local/bin/join.sh':
#        require => [File['/etc/smb.pwd'],
#                    File['/etc/samba/smb.conf'],
#                    File['/usr/local/bin/join.sh']],
#        subscribe => [File['/etc/smb.pwd'],
#                      File['/etc/samba/smb.conf'],
#                      File['/usr/local/bin/join.sh']],
#        refreshonly => true,
#    }

    exec { 'join':
        command => '/usr/bin/net ads join -U unix_manager < /etc/smb.pwd',
        require => [File['/etc/smb.pwd'],
                    File['/etc/samba/smb.conf']],
        subscribe => [File['/etc/smb.pwd'],
                      File['/etc/samba/smb.conf']],
        refreshonly => true,
    }

    service { 'samba':
        ensure => running,
        enable => true,
        require => [File['/etc/smb.pwd'],
                    File['/etc/samba/smb.conf']],
        subscribe => [File['/etc/smb.pwd'],
                      File['/etc/samba/smb.conf'],
                      Exec['join']],
    }
}
