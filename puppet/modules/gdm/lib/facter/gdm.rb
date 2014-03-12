Facter.add("gdm") do
  setcode do
    Facter::Util::Resolution.exec('/usr/bin/dpkg -s gdm 2>/dev/null')
  end
end
