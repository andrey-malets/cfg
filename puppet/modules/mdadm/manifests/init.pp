class mdadm {
    if $mdadm == 'true' {
        augeas { 'mdadm':
            context => '/files/etc/mdadm/mdadm.conf',
            changes => "set mailaddr/value $mdadm_admin",
        }
    }
}
