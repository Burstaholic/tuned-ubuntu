%bcond_with snapshot

%if %{with snapshot}
%if 0%{!?git_short_commit:1}
%global git_short_commit %(git rev-parse --short=8 --verify HEAD)
%endif
%global git_date %(date +'%Y%m%d')
%global git_suffix %{git_date}git%{git_short_commit}
%endif

Summary: A dynamic adaptive system tuning daemon
Name: tuned
Version: 2.6.0
Release: 1%{?with_snapshot:.%{git_suffix}}%{?dist}
License: GPLv2+
Source: https://fedorahosted.org/releases/t/u/tuned/tuned-%{version}.tar.bz2
URL: https://fedorahosted.org/tuned/
BuildArch: noarch
BuildRequires: python, systemd, desktop-file-utils
Requires(post): systemd, virt-what
Requires(preun): systemd
Requires(postun): systemd
Requires: python-decorator, dbus-python, pygobject3-base, python-pyudev
Requires: virt-what, python-configobj, ethtool, gawk, kernel-tools, hdparm
Requires: util-linux, python-perf

%description
The tuned package contains a daemon that tunes system settings dynamically.
It does so by monitoring the usage of several system components periodically.
Based on that information components will then be put into lower or higher
power saving modes to adapt to the current usage. Currently only ethernet
network and ATA harddisk devices are implemented.

%if 0%{?rhel} <= 7 && 0%{!?fedora:1}
# RHEL <= 7
%global docdir %{_docdir}/%{name}-%{version}
%else
# RHEL > 7 || fedora
%global docdir %{_docdir}/%{name}
%endif

%package gtk
Summary: GTK GUI for tuned
Requires: %{name} = %{version}-%{release}
Requires: powertop, pygobject3-base, polkit

%description gtk
GTK GUI that can control tuned and provides simple profile editor.

%package utils
Requires: %{name} = %{version}-%{release}
Requires: powertop
Summary: Various tuned utilities

%description utils
This package contains utilities that can help you to fine tune and
debug your system and manage tuned profiles.

%package utils-systemtap
Summary: Disk and net statistic monitoring systemtap scripts
Requires: %{name} = %{version}-%{release}
Requires: systemtap

%description utils-systemtap
This package contains several systemtap scripts to allow detailed
manual monitoring of the system. Instead of the typical IO/sec it collects
minimal, maximal and average time between operations to be able to
identify applications that behave power inefficient (many small operations
instead of fewer large ones).

%package profiles-sap
Summary: Additional tuned profile(s) targeted to SAP NetWeaver loads
Requires: %{name} = %{version}-%{release}

%description profiles-sap
Additional tuned profile(s) targeted to SAP NetWeaver loads.

%package profiles-oracle
Summary: Additional tuned profile(s) targeted to Oracle loads
Requires: %{name} = %{version}-%{release}

%description profiles-oracle
Additional tuned profile(s) targeted to Oracle loads.

%package profiles-sap-hana
Summary: Additional tuned profile(s) targeted to SAP HANA loads
Requires: %{name} = %{version}-%{release}

%description profiles-sap-hana
Additional tuned profile(s) targeted to SAP HANA loads.

%package profiles-atomic
Summary: Additional tuned profile(s) targeted to Atomic
Requires: %{name} = %{version}-%{release}

%description profiles-atomic
Additional tuned profile(s) targeted to Atomic host and guest.

%package profiles-realtime
Summary: Additional tuned profile(s) targeted to realtime
Requires: %{name} = %{version}-%{release}
Requires: tuna

%description profiles-realtime
Additional tuned profile(s) targeted to realtime.

%package profiles-nfv
Summary: Additional tuned profile(s) targeted to Network Function Virtualization (NFV)
Requires: %{name} = %{version}-%{release}
Requires: %{name}-profiles-realtime = %{version}-%{release}
Requires: tuna, qemu-kvm-tools-rhev

%description profiles-nfv
Additional tuned profile(s) targeted to Network Function Virtualization (NFV).

%package profiles-compat
Summary: Additional tuned profiles mainly for backward compatibility with tuned 1.0
Requires: %{name} = %{version}-%{release}

%description profiles-compat
Additional tuned profiles mainly for backward compatibility with tuned 1.0.
It can be also used to fine tune your system for specific scenarios.

%prep
%setup -q


%build


%install
make install DESTDIR=%{buildroot} DOCDIR=%{docdir}
%if 0%{?rhel}
sed -i 's/\(dynamic_tuning[ \t]*=[ \t]*\).*/\10/' %{buildroot}%{_sysconfdir}/tuned/tuned-main.conf
%endif

# conditional support for grub2, grub2 is not available on all architectures
# and tuned is noarch package, thus the following hack is needed
mkdir -p %{buildroot}%{_datadir}/tuned/grub2
mv %{buildroot}%{_sysconfdir}/grub.d/00_tuned %{buildroot}%{_datadir}/tuned/grub2/00_tuned
rmdir %{buildroot}%{_sysconfdir}/grub.d

# ghost for NFV
mkdir -p %{buildroot}%{_sysconfdir}/modprobe.d
touch %{buildroot}%{_sysconfdir}/modprobe.d/kvm.rt.tuned.conf

# validate desktop file
desktop-file-validate %{buildroot}%{_datadir}/applications/tuned-gui.desktop

%post
%systemd_post tuned.service

# convert active_profile from full path to name (if needed)
sed -i 's|.*/\([^/]\+\)/[^\.]\+\.conf|\1|' /etc/tuned/active_profile

# convert GRUB_CMDLINE_LINUX to GRUB_CMDLINE_LINUX_DEFAULT
if [ -r "%{_sysconfdir}/default/grub" ]; then
  sed -i 's/GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX \\$tuned_params"/GRUB_CMDLINE_LINUX_DEFAULT="$GRUB_CMDLINE_LINUX_DEFAULT \\$tuned_params"/' \
    %{_sysconfdir}/default/grub
fi


%preun
%systemd_preun tuned.service


%postun
%systemd_postun_with_restart tuned.service

# conditional support for grub2, grub2 is not available on all architectures
# and tuned is noarch package, thus the following hack is needed
if [ "$1" == 0 ]; then
  rm -f %{_sysconfdir}/grub.d/00_tuned || :
# unpatch /etc/default/grub
  if [ -r "%{_sysconfdir}/default/grub" ]; then
    sed -i '/GRUB_CMDLINE_LINUX_DEFAULT="${GRUB_CMDLINE_LINUX_DEFAULT:+$GRUB_CMDLINE_LINUX_DEFAULT }\\$tuned_params"/d' %{_sysconfdir}/default/grub
  fi
fi


%triggerun -- tuned < 2.0-0
# remove ktune from old tuned, now part of tuned
/usr/sbin/service ktune stop &>/dev/null || :
/usr/sbin/chkconfig --del ktune &>/dev/null || :


%posttrans
# conditional support for grub2, grub2 is not available on all architectures
# and tuned is noarch package, thus the following hack is needed
if [ -d %{_sysconfdir}/grub.d ]; then
  cp -a %{_datadir}/tuned/grub2/00_tuned %{_sysconfdir}/grub.d/00_tuned
fi


%post gtk
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :


%postun gtk
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :
fi


%posttrans gtk
/usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :


%files
%defattr(-,root,root,-)
%exclude %{docdir}/README.utils
%exclude %{docdir}/README.scomes
%doc %{docdir}
%{_datadir}/bash-completion/completions/tuned-adm
%exclude %{python_sitelib}/tuned/gtk
%{python_sitelib}/tuned
%{_sbindir}/tuned
%{_sbindir}/tuned-adm
%exclude %{_sysconfdir}/tuned/realtime-variables.conf
%exclude %{_prefix}/lib/tuned/default
%exclude %{_prefix}/lib/tuned/desktop-powersave
%exclude %{_prefix}/lib/tuned/laptop-ac-powersave
%exclude %{_prefix}/lib/tuned/server-powersave
%exclude %{_prefix}/lib/tuned/laptop-battery-powersave
%exclude %{_prefix}/lib/tuned/enterprise-storage
%exclude %{_prefix}/lib/tuned/spindown-disk
%exclude %{_prefix}/lib/tuned/sap-netweaver
%exclude %{_prefix}/lib/tuned/sap-hana
%exclude %{_prefix}/lib/tuned/sap-hana-vmware
%exclude %{_prefix}/lib/tuned/oracle
%exclude %{_prefix}/lib/tuned/atomic-host
%exclude %{_prefix}/lib/tuned/atomic-guest
%exclude %{_prefix}/lib/tuned/realtime
%exclude %{_prefix}/lib/tuned/realtime-virtual-guest
%exclude %{_prefix}/lib/tuned/realtime-virtual-host
%{_prefix}/lib/tuned
%dir %{_sysconfdir}/tuned
%dir %{_libexecdir}/tuned
%config(noreplace) %verify(not size mtime md5) %{_sysconfdir}/tuned/active_profile
%config(noreplace) %{_sysconfdir}/tuned/tuned-main.conf
%config(noreplace) %verify(not size mtime md5) %{_sysconfdir}/tuned/bootcmdline
%{_sysconfdir}/dbus-1/system.d/com.redhat.tuned.conf
%{_tmpfilesdir}/tuned.conf
%{_unitdir}/tuned.service
%dir %{_localstatedir}/log/tuned
%dir /run/tuned
%{_mandir}/man5/tuned*
%{_mandir}/man7/tuned-profiles.7*
%{_mandir}/man8/tuned*
%dir %{_datadir}/tuned
%{_datadir}/tuned/grub2

%files gtk
%defattr(-,root,root,-)
%{_sbindir}/tuned-gui
%{python_sitelib}/tuned/gtk
%{_datadir}/tuned/ui
%{_datadir}/polkit-1/actions/org.tuned.gui.policy
%{_datadir}/icons/hicolor/scalable/apps/tuned.svg
%{_datadir}/applications/tuned-gui.desktop

%files utils
%doc COPYING
%{_bindir}/powertop2tuned
%{_libexecdir}/tuned/pmqos-static*

%files utils-systemtap
%defattr(-,root,root,-)
%doc doc/README.utils
%doc doc/README.scomes
%doc COPYING
%{_sbindir}/varnetload
%{_sbindir}/netdevstat
%{_sbindir}/diskdevstat
%{_sbindir}/scomes
%{_mandir}/man8/varnetload.*
%{_mandir}/man8/netdevstat.*
%{_mandir}/man8/diskdevstat.*
%{_mandir}/man8/scomes.*

%files profiles-sap
%defattr(-,root,root,-)
%{_prefix}/lib/tuned/sap-netweaver
%{_mandir}/man7/tuned-profiles-sap.7*

%files profiles-sap-hana
%defattr(-,root,root,-)
%{_prefix}/lib/tuned/sap-hana
%{_prefix}/lib/tuned/sap-hana-vmware
%{_mandir}/man7/tuned-profiles-sap-hana.7*

%files profiles-oracle
%defattr(-,root,root,-)
%{_prefix}/lib/tuned/oracle
%{_mandir}/man7/tuned-profiles-oracle.7*

%files profiles-atomic
%defattr(-,root,root,-)
%{_prefix}/lib/tuned/atomic-host
%{_prefix}/lib/tuned/atomic-guest
%{_mandir}/man7/tuned-profiles-atomic.7*

%files profiles-realtime
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/tuned/realtime-variables.conf
%{_prefix}/lib/tuned/realtime
%{_mandir}/man7/tuned-profiles-realtime.7*

%files profiles-nfv
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/tuned/realtime-virtual-guest-variables.conf
%config(noreplace) %{_sysconfdir}/tuned/realtime-virtual-host-variables.conf
%ghost %{_sysconfdir}/modprobe.d/kvm.rt.tuned.conf
%{_prefix}/lib/tuned/realtime-virtual-guest
%{_prefix}/lib/tuned/realtime-virtual-host
%{_libexecdir}/tuned/defirqaffinity*
%{_mandir}/man7/tuned-profiles-nfv.7*

%files profiles-compat
%defattr(-,root,root,-)
%{_prefix}/lib/tuned/default
%{_prefix}/lib/tuned/desktop-powersave
%{_prefix}/lib/tuned/laptop-ac-powersave
%{_prefix}/lib/tuned/server-powersave
%{_prefix}/lib/tuned/laptop-battery-powersave
%{_prefix}/lib/tuned/enterprise-storage
%{_prefix}/lib/tuned/spindown-disk
%{_mandir}/man7/tuned-profiles-compat.7*

%changelog
* Tue Jan  5 2016 Jaroslav Škarvada <jskarvad@redhat.com> - 2.6.0-1
- new-release
  - plugin_cpu: do not show error if cpupower or x86_energy_perf_policy are missing
  - plugin_sysctl: fixed quoting of sysctl values
    resolves: rhbz#1254538
  - tuned-adm: added log file location hint to verify command output
  - libexec: fixed listdir and isdir in defirqaffinity.py
    resolves: rhbz#1252160
  - plugin_cpu: save and restore only intel pstate attributes that were changed
    resolves: rhbz#1252156
  - functions: fixed sysfs save to work with options
    resolves: rhbz#1251507
  - plugins: added scsi_host plugin
  - tuned-adm: fixed restart attempt if tuned is not running
  - spec: fixed post scriptlet to work without grub
    resolves: rhbz#1265654
  - tuned-profiles-nfv: fix find-lapictscdeadline-optimal.sh for CPUS where ns > 6500
    resolves: rhbz#1267284
  - functions: fixed restore_logs_syncing to preserve SELinux context on rsyslog.conf
    resolves: rhbz#1268901
  - realtime: set unboud workqueues cpumask
    resolves: rhbz#1259043
  - spec: correctly remove tuned footprint from /etc/default/grub
    resolves: rhbz#1268845
  - gui: fixed creation of new profile
    resolves: rhbz#1274609
  - profiles: removed nohz_full from the realtime profile
    resolves: rhbz#1274486
  - profiles: Added nohz_full and nohz=on to realtime guest/host profiles
    resolves: rhbz#1274445
  - profiles: fixed lapic_timer_adv_ns cache
    resolves: rhbz#1259452
  - plugin_sysctl: pass verification even if the option doesn't exist
    related: rhbz#1252153
  - added support for 'summary' and 'description' of profiles,
    extended D-Bus API for Cockpit
    related: rhbz#1228356

* Tue Aug  4 2015 Jaroslav Škarvada <jskarvad@redhat.com> - 2.5.1-1
- new-release
  related: rhbz#1155052
  - plugin_scheduler: work with nohz_full
    resolves: rhbz#1247184
  - fixed realtime-virtual-guest/host profiles packaged twice
    resolves: rhbz#1249028
  - fixed requirements of realtime and nfv profiles
  - fixed tuned-gui not starting
  - various other minor fixes

* Sun Jul  5 2015 Jaroslav Škarvada <jskarvad@redhat.com> - 2.5.0-1
- new-release
  resolves: rhbz#1155052
  - add support for ethtool -C to tuned network plugin
    resolves: rhbz#1152539
  - add support for ethtool -K to tuned network plugin
    resolves: rhbz#1152541
  - add support for calculation of values for the kernel command line
    resolves: rhbz#1191595
  - no error output if there is no hdparm installed
    resolves: rhbz#1191775
  - do not run hdparm on hotplug events if there is no hdparm tuning
    resolves: rhbz#1193682
  - add oracle tuned profile
    resolves: rhbz#1196298
  - fix bash completions for tuned-adm
    resolves: rhbz#1207668
  - add glob support to tuned sysfs plugin
    resolves: rhbz#1212831
  - add tuned-adm verify subcommand
    resolves: rhbz#1212836
  - do not install tuned kernel command line to rescue kernels
    resolves: rhbz#1223864
  - add variables support
    resolves: rhbz#1225124
  - add built-in support for unit conversion into tuned
    resolves: rhbz#1225135
  - fix vm.max_map_count setting in sap-netweaver profile
    resolves: rhbz#1228562
  - add tuned profile for RHEL-RT
    resolves: rhbz#1228801
  - plugin_scheduler: added support for runtime tuning of processes
    resolves: rhbz#1148546
  - add support for changing elevators on xvd* devices (Amazon EC2)
    resolves: rhbz#1170152
  - add workaround to be run after systemd-sysctl
    resolves: rhbz#1189263
  - do not change settings of transparent hugepages if set in kernel cmdline
    resolves: rhbz#1189868
  - add tuned profiles for RHEL-NFV
    resolves: rhbz#1228803
  - plugin_bootloader: apply $tuned_params to existing kernels
    resolves: rhbz#1233004

* Thu Oct 16 2014 Jaroslav Škarvada <jskarvad@redhat.com> - 2.4.1-1
- new-release
  - fixed return code of tuned grub template
    resolves: rhbz#1151768
  - plugin_bootloader: fix for multiple parameters on command line
    related: rhbz#1148711
  - tuned-adm: fixed traceback on "tuned-adm list"
    resolves: rhbz#1149162
  - plugin_bootloader is automatically disabled if grub2 is not found
    resolves: rhbz#1150047
  - plugin_disk: set_spindown and set_APM made independent
    resolves: rhbz#976725

* Wed Oct  1 2014 Jaroslav Škarvada <jskarvad@redhat.com> - 2.4.0-1
- new-release
  resolves: rhbz#1093883
  - fixed traceback if profile cannot be loaded
    related: rhbz#953128
  - powertop2tuned: fixed traceback if rewriting file instead of dir
    resolves: rhbz#963441
  - daemon: fixed race condition in start/stop
  - improved timings, it can be fine tuned in /etc/tuned/tuned-main.conf
    resolves: rhbz#1028122
  - throughput-performance: altered dirty ratios for better performance
    resolves: rhbz#1043533
  - latency-performance: leaving THP on its default
    resolves: rhbz#1064510
  - used throughput-performance profile on server by default
    resolves: rhbz#1063481
  - network-latency: added new profile
    resolves: rhbz#1052418
  - network-throughput: added new profile
    resolves: rhbz#1052421
  - recommend.conf: fixed config file
    resolves: rhbz#1069123
  - spec: added kernel-tools requirement
    resolves: rhbz#1073008
  - systemd: added cpupower.service conflict
    resolves: rhbz#1073392
  - balanced: used medium_power ALPM policy
  - added support for >, < assignment modifiers in tuned.conf
  - handled root block devices
  - balanced: used conservative CPU governor
    resolves: rhbz#1124125
  - plugins: added selinux plugin
  - plugin_net: added nf_conntrack_hashsize parameter
  - profiles: added atomic-host profile
    resolves: rhbz#1091977
  - profiles: added atomic-guest profile
    resolves: rhbz#1091979
  - moved profile autodetection from post install script to tuned daemon
    resolves: rhbz#1144067
  - profiles: included sap-hana and sap-hana-vmware profiles
  - man: structured profiles manual pages according to sub-packages
  - added missing hdparm dependency
    resolves: rhbz#1144858
  - improved error handling of switch_profile
    resolves: rhbz#1068699
  - tuned-adm: active: detect whether tuned deamon is running
    related: rhbz#1068699
  - removed active_profile from RPM verification
    resolves: rhbz#1104126
  - plugin_disk: readahead value can be now specified in sectors
    resolves: rhbz#1127127
  - plugins: added bootloader plugin
    resolves: rhbz#1044111
  - plugin_disk: added error counter to hdparm calls
  - plugins: added scheduler plugin
    resolves: rhbz#1100826
  - added tuned-gui

* Wed Nov  6 2013 Jaroslav Škarvada <jskarvad@redhat.com> - 2.3.0-1
- new-release
  resolves: rhbz#1020743
  - audio plugin: fixed audio settings in standard profiles
    resolves: rhbz#1019805
  - video plugin: fixed tunings
  - daemon: fixed crash if preset profile is not available
    resolves: rhbz#953128
  - man: various updates and corrections
  - functions: fixed usb and bluetooth handling
  - tuned: switched to lightweighted pygobject3-base
  - daemon: added global config for dynamic_tuning
    resolves: rhbz#1006427
  - utils: added pmqos-static script for debug purposes
    resolves: rhbz#1015676
  - throughput-performance: various fixes
    resolves: rhbz#987570
  - tuned: added global option update_interval
  - plugin_cpu: added support for x86_energy_perf_policy
    resolves: rhbz#1015675
  - dbus: fixed KeyboardInterrupt handling
  - plugin_cpu: added support for intel_pstate
    resolves: rhbz#996722
  - profiles: various fixes
    resolves: rhbz#922068
  - profiles: added desktop profile
    resolves: rhbz#996723
  - tuned-adm: implemented non DBus fallback control
  - profiles: added sap profile
  - tuned: lowered CPU usage due to python bug
    resolves: rhbz#917587

* Tue Mar 19 2013 Jaroslav Škarvada <jskarvad@redhat.com> - 2.2.2-1
- new-release:
  - cpu plugin: fixed cpupower workaround
  - cpu plugin: fixed crash if cpupower is installed

* Fri Mar  1 2013 Jaroslav Škarvada <jskarvad@redhat.com> - 2.2.1-1
- new release:
  - audio plugin: fixed error handling in _get_timeout
  - removed cpupower dependency, added sysfs fallback
  - powertop2tuned: fixed parser crash on binary garbage
    resolves: rhbz#914933
  - cpu plugin: dropped multicore_powersave as kernel upstream already did
  - plugins: options manipulated by dynamic tuning are now correctly saved and restored
  - powertop2tuned: added alias -e for --enable option
  - powertop2tuned: new option -m, --merge-profile to select profile to merge
  - prefer transparent_hugepage over redhat_transparent_hugepage
  - recommend: use recommend.conf not autodetect.conf
  - tuned.service: switched to dbus type service
    resolves: rhbz#911445
  - tuned: new option --pid, -P to write PID file
  - tuned, tuned-adm: added new option --version, -v to show version
  - disk plugin: use APM value 254 for cleanup / APM disable instead of 255
    resolves: rhbz#905195
  - tuned: new option --log, -l to select log file
  - powertop2tuned: avoid circular deps in include (one level check only)
  - powertop2tuned: do not crash if powertop is not installed
  - net plugin: added support for wake_on_lan static tuning
    resolves: rhbz#885504
  - loader: fixed error handling
  - spec: used systemd-rpm macros
    resolves: rhbz#850347

* Mon Jan 28 2013 Jan Vcelak <jvcelak@redhat.com> 2.2.0-1
- new release:
  - remove nobarrier from virtual-guest (data loss prevention)
  - devices enumeration via udev, instead of manual retrieval
  - support for dynamically inserted devices (currently disk plugin)
  - dropped rfkill plugins (bluetooth and wifi), the code didn't work

* Wed Jan  2 2013 Jaroslav Škarvada <jskarvad@redhat.com> - 2.1.2-1
- new release:
  - systemtap {disk,net}devstat: fix typo in usage
  - switched to configobj parser
  - latency-performance: disabled THP
  - fixed fd leaks on subprocesses

* Thu Dec 06 2012 Jan Vcelak <jvcelak@redhat.com> 2.1.1-1
- fix: powertop2tuned execution
- fix: ownership of /etc/tuned

* Mon Dec 03 2012 Jan Vcelak <jvcelak@redhat.com> 2.1.0-1
- new release:
  - daemon: allow running without selected profile
  - daemon: fix profile merging, allow only safe characters in profile names
  - daemon: implement missing methods in DBus interface
  - daemon: implement profile recommendation
  - daemon: improve daemonization, PID file handling
  - daemon: improved device matching in profiles, negation possible
  - daemon: various internal improvements
  - executables: check for EUID instead of UID
  - executables: run python with -Es to increase security
  - plugins: cpu - fix cpupower execution
  - plugins: disk - fix option setting
  - plugins: mounts - new, currently supports only barriers control
  - plugins: sysctl - fix a bug preventing settings application
  - powertop2tuned: speedup, fix crashes with non-C locales
  - powertop2tuned: support for powertop 2.2 output
  - profiles: progress on replacing scripts with plugins
  - tuned-adm: bash completion - suggest profiles from all supported locations
  - tuned-adm: complete switch to D-bus
  - tuned-adm: full control to users with physical access

* Mon Oct 08 2012 Jaroslav Škarvada <jskarvad@redhat.com> - 2.0.2-1
- New version
- Systemtap scripts moved to utils-systemtap subpackage

* Sun Jul 22 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 12 2012 Jaroslav Škarvada <jskarvad@redhat.com> - 2.0.1-3
- another powertop-2.0 compatibility fix
  Resolves: rhbz#830415

* Tue Jun 12 2012 Jan Kaluza <jkaluza@redhat.com> - 2.0.1-2
- fixed powertop2tuned compatibility with powertop-2.0

* Tue Apr 03 2012 Jaroslav Škarvada <jskarvad@redhat.com> - 2.0.1-1
- new version

* Fri Mar 30 2012 Jan Vcelak <jvcelak@redhat.com> 2.0-1
- first stable release
