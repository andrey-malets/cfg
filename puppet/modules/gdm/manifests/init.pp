class gdm {
    if $gdm =~ /^Package/ {
        service { 'gdm':
        }
    } else {
        service { 'gdm':
            status => '/bin/true',
            start => '/bin/true',
            stop => '/bin/true',
            restart => '/bin/true',
        }
    }
}
