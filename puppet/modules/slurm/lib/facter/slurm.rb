Facter.add(:slurm) do
    setcode do
        Facter::Util::Resolution.exec('/usr/sbin/slurmd -C | head -n1')
    end
end
