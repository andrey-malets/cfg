Facter.add("pyxendomains") do
  confine :virtual => 'xen0'
  setcode do
    Facter::Util::Resolution.exec('/var/lib/puppet/lib/facter/util/xendomains.py')
  end
end
