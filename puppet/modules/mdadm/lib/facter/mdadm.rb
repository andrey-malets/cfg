Facter.add("mdadm") do
  setcode do
    File.exists?("/etc/mdadm/mdadm.conf")
  end
end
