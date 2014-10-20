Facter.add("pyxendomains") do
  confine :virtual => 'xen0'
  setcode do
    Facter::Util::Resolution.exec('/usr/local/bin/xendomains.py')
  end
end
