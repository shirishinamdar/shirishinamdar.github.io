---
title: Hands-On with Metasploit and the EC-Council STORM Kit
date: 2026-05-10 18:54:00 -0400
categories: [Offensive Security]
tags: [Metasploit, STORM Kit, Raspberry Pi, Offensive Security, Lab]
description: Unboxing the EC-Council STORM kit (a Raspberry Pi-based mobile pentest platform), then running the first Metasploit framework lab from a Kali VM against an intentionally vulnerable target.
image:
  path: /assets/img/blog/metasploit-storm-kit/cover.svg
  alt: "METASPLOIT — msfconsole + EC-Council STORM Kit"
---

# Overview

This week's work focused on three main tasks:

  - Unboxing, powering up, and assessing the EC-Council STORM
    cybersecurity toolkit a Raspberry Pi-based mobile security tool kit
    to check its current OS version and determine whether an update was
    needed.

  - Completing a full hardware inventory of NVCC-donated equipment
    located in room IET AL AA427 Any issues identified during the
    inventory process were resolved with my assistance.

  - Beginning hands-on Metasploit lab work using a Kali Linux VM and a
    Metasploitable 2 target VM running in VMware Workstation, covering
    network reconnaissance and exploitation of a known vulnerability.

# EC-Council STORM Kit Setup & Assessment

The first step was to unbox the EC-Council STORM Kit and inspect its
physical label. The label contained all critical device information
including the serial number (110352771262), the order number, the
default login credentials (username: pi, password: storm2021), and
confirmation that no expansion pack was included. This information was
recorded before proceeding with powering on the device.

![](/assets/img/blog/metasploit-storm-kit/image1.jpg)

*Figure 1 -- EC-Council STORM Kit label showing serial number, order
number, login credentials, and expansion pack status.*

The device was then connected to a display and powered on. The Raspberry
Pi login screen appeared, running the LXDE desktop environment on
Raspbian. The username 'pi' was pre-selected and the password
'storm2021' from the label was entered to authenticate into the system.

![](/assets/img/blog/metasploit-storm-kit/image2.jpg)

*Figure 2 -- Raspberry Pi login screen prompting for the password before
accessing the STORM desktop environment.*

After logging in successfully, the full physical workspace was set up
with both a standard keyboard and the included flexible rubber keyboard
connected to the Raspberry Pi. The STORM login screen was visible on the
attached display, confirming the device was operational and ready for
further configuration steps.

![](/assets/img/blog/metasploit-storm-kit/image3.jpg)

*Figure 3 -- Full physical setup showing the Raspberry Pi device,
attached display with login screen, and keyboards connected.*

To verify the exact operating system version running on the device, the
terminal was opened and the command 'cat /etc/os-release' was executed.
The output confirmed the device is running Raspbian GNU/Linux 10
(Buster). This information is important for determining compatibility
with newer tools and assessing whether an OS upgrade to a more recent
version of Raspberry Pi OS is required.

![](/assets/img/blog/metasploit-storm-kit/image4.jpg)

# *Figure 4 -- Terminal output of 'cat /etc/os-release' confirming Raspbian GNU/Linux 10 (Buster) as the current OS version*

When I checked cat /etc/os-release, it showed that the system is still
running an older version. The kit is currently not connected to the
internet, and it needs to be updated to the latest version.

# 

# NVCC Donation Inventory 

In addition to the STORM kit work, a full inventory was initiated for
the NVCC-donated hardware stored in room IET AL AA427. The inventory
covered two categories of equipment: 20 units of the Dell OptiPlex 7090
SFF desktop computers and 20 units of the Dell Latitude 5420 laptops,
bringing the total to 40 devices catalogued. Each unit was logged with
its service tag, express service code, model, location, assigned user,
and current status. Any issues found during the verification process
such as unreadable or mismatched express service codes were flagged and
subsequently cleared in coordination with work study. The inventory
spreadsheet was updated as of March 10, 2026 and reflects the current
state of all donated assets.

# 

# Metasploitable Lab : Penetration Testing Practice

Hands-on penetration testing lab work was begun using two virtual
machines running in VMware Workstation: a Kali Linux VM as the attacker
machine and a Metasploitable 2 VM as the intentionally vulnerable
target. This lab environment is used for practicing ethical hacking and
offensive security techniques in a safe, isolated network.(Host-Only)

## Identifying the Target IP Address

The Metasploitable 2 VM was booted and logged into with the default
credentials. The command 'ip a' was run to identify the machine's IP
address on the local network. The target was confirmed to be reachable
at IP address 192.168.146.130 on the eth0 interface, which would be used
as the target for all subsequent scanning and exploitation activity.

![](/assets/img/blog/metasploit-storm-kit/image5.jpg)

*Figure 6 -- Metasploitable 2 VM showing the output of 'ip a', confirming
the target IP address as 192.168.146.130.*

## Nmap Service Version Scan

From the Kali Linux VM, an Nmap service version scan was launched
against the Metasploitable 2 target using the command 'sudo nmap -sV
192.168.146.130'. The scan completed and revealed a large number of open
ports and running services. Notable findings included vsftpd 2.3.4 on
port 21 (a version known to contain a backdoor vulnerability), OpenSSH
on port 22, Apache HTTP on port 80, MySQL on port 3306, PostgreSQL on
port 5432, VNC on port 5900, and many others. This reconnaissance step
provided a full picture of the attack surface available on the target
machine.

![](/assets/img/blog/metasploit-storm-kit/image6.jpg)

*Figure 7 -- Nmap -sV scan results against 192.168.146.130, revealing all
open ports and service versions including the vulnerable vsftpd 2.3.4.*

## Launching Metasploit Framework

Metasploit's msfconsole is the primary interface for selecting,
configuring, and launching exploit modules against target systems.

![](/assets/img/blog/metasploit-storm-kit/image7.jpg)

*Figure 8 -- Metasploit Framework msfconsole successfully launched on
Kali Linux, showing version 6.4.112-dev and available module counts.*

## Exploiting the vsftpd 2.3.4 Backdoor

The vsftpd 2.3.4 backdoor exploit module
(exploit/unix/ftp/vsftpd_234_backdoor) was selected using 'use 1'
after searching for vsftpd modules. The output confirmed UID 0 (root)
and GID 0 (root), meaning full administrative access to the
Metasploitable 2 system was achieved. Running 'ls' and 'hostname'
commands confirmed the shell was operating on the metasploitable target
filesystem.

![](/assets/img/blog/metasploit-storm-kit/image8.jpg)

*Figure 9 -- Metasploit vsftpd_234_backdoor exploit successfully
executed, resulting in a root shell on the Metasploitable 2 target at
192.168.146.130.*
