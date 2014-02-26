Facter.add("slurm") do
  setcode do
    Facter::Util::Resolution.exec('/usr/sbin/slurmd -C')
  end
end
