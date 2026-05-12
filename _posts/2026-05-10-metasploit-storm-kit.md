---
title: "Exploiting Metasploitable 2 with Metasploit Framework"
date: 2026-05-10 18:54:00 -0400
categories: [Offensive Security]
tags: [Metasploit, Metasploitable, Nmap, vsftpd, Kali Linux, Raspberry Pi, Lab]
description: Reconnaissance and exploitation of an intentionally vulnerable Metasploitable 2 target from Kali Linux — Nmap service-version scan, locating the vsftpd 2.3.4 backdoor, and using the corresponding Metasploit module to land a root shell.
image:
  path: /assets/img/blog/metasploit-storm-kit/image7.jpg
  alt: "Metasploit Framework msfconsole launched on Kali Linux."
---

> Everything below was performed against **Metasploitable 2**, an intentionally vulnerable virtual machine designed for offensive-security practice, on an isolated host-only network. Running these techniques against any system you do not own or have explicit written authorization to test is a crime in most jurisdictions, including the U.S. (Computer Fraud and Abuse Act), the UK (Computer Misuse Act 1990), and India (IT Act, Section 66).
{: .prompt-warning }

Metasploitable 2 is calibrated to fall. Every service on it has a known vulnerability, every CVE has a matching Metasploit module, and the whole thing exists so you can practice the offensive-security workflow against a target that won't fight back.

This post is my walkthrough of that workflow against Metasploitable 2 from a Kali Linux attacker VM: Nmap reconnaissance, identifying the famous vsftpd 2.3.4 backdoor in the service-version output, and using the matching Metasploit module to land a root shell. Along the way I also assessed an EC-Council STORM kit — a Raspberry Pi-based portable pentest platform — as a secondary attacker reference.

---

## Background: The Three Tools

| Tool | Role |
| --- | --- |
| **Metasploitable 2** | A deliberately vulnerable Linux VM published by Rapid7. Hosts old versions of vsftpd, Samba, MySQL, Tomcat, Apache, and others, each with documented CVEs. The standard target for early Metasploit practice. |
| **Nmap** | Network mapper. Used here in `-sV` (service/version detection) mode to identify what's listening on each open port and at what version. |
| **Metasploit Framework** | Offensive-security framework. Bundles thousands of exploit modules indexed by CVE, vendor, and protocol, with a consistent `set OPTION value → run` workflow. Driven from `msfconsole`. |

Underneath all of this is a simple loop: *find a service, look up known vulnerabilities for its version, pick a matching exploit, point it at the target, and see if you get code execution.* Metasploitable 2 is calibrated so that every step in this loop succeeds — useful for learning the workflow, not representative of how hardened systems behave.

---

## Lab Setup

| Item | Detail |
| --- | --- |
| Hypervisor | VMware Workstation |
| Attacker VM | Kali Linux (rolling), interface `eth0` |
| Target VM | Metasploitable 2, IP `192.168.146.130` on `eth0` |
| Network | Host-only, isolated from internet and other VMs |
| Additional reference | EC-Council STORM kit (Raspberry Pi, Raspbian 10 Buster) |

Host-only networking is the important detail. Metasploitable 2 is dangerous to expose anywhere — its known-vulnerable services would be compromised within minutes on a routable network.

---

## 1. EC-Council STORM Kit — Initial Assessment

Before the Metasploit lab itself, the STORM kit was set up as a secondary reference platform. The kit is a Raspberry Pi pre-imaged with EC-Council's customized Raspbian build, packaged as a portable pentest workstation.

![Raspberry Pi login screen on the STORM kit at first boot.](/assets/img/blog/metasploit-storm-kit/image2.jpg)

The kit ships with publicly documented default credentials (`pi` / `storm2021`). On any device used outside a sealed lab, those credentials are the first thing to change.

![STORM kit booted to its desktop environment with peripherals attached.](/assets/img/blog/metasploit-storm-kit/image3.jpg)

The first technical task was to determine which OS version was actually on the device, so any planned tool installs could be checked for compatibility:

```bash
cat /etc/os-release
```

Output confirmed **Raspbian GNU/Linux 10 (Buster)**:

![/etc/os-release output showing Raspbian 10 (Buster) on the STORM kit.](/assets/img/blog/metasploit-storm-kit/image4.jpg)

Buster reached end-of-life in mid-2024. Anything depending on current OpenSSL, current `apt` repositories, or modern Python packaging will not install cleanly without backports or an upgrade to a newer Raspberry Pi OS release. The kit also shipped offline, so the upgrade itself becomes a follow-up task before the kit is genuinely usable.

---

## 2. Identifying the Target on the Network

On the Metasploitable VM, the target's IP address is verified directly:

```bash
ip a
```

The relevant line shows `inet 192.168.146.130/24` on `eth0`. That's the address that will be used as the target for every step below.

![Metasploitable 2 showing its eth0 address as 192.168.146.130.](/assets/img/blog/metasploit-storm-kit/image5.jpg)

---

## 3. Reconnaissance — Nmap Service-Version Scan

From the Kali attacker, a service-version scan is launched against the target:

```bash
sudo nmap -sV 192.168.146.130
```

Flag-by-flag:

- `sudo` — Nmap needs root for the SYN scan, which uses raw sockets.
- `-sV` — service/version detection. Instead of just reporting "port 21 open," Nmap negotiates with each service and prints what's actually listening and at what version.

Metasploitable 2 lights up with a long list of open ports and identifiable services:

| Port | Service | Version (relevant) |
| --- | --- | --- |
| 21 | FTP | **vsftpd 2.3.4** |
| 22 | SSH | OpenSSH 4.7p1 |
| 23 | Telnet | linux telnetd |
| 25 | SMTP | Postfix smtpd |
| 80 | HTTP | Apache 2.2.8 |
| 139, 445 | SMB | Samba 3.x |
| 3306 | MySQL | 5.0.51a |
| 5432 | PostgreSQL | 8.3.0 |
| 5900 | VNC | RealVNC |

![Nmap -sV results revealing vsftpd 2.3.4 and other vulnerable services.](/assets/img/blog/metasploit-storm-kit/image6.jpg)

The **vsftpd 2.3.4** entry is the one that ends the lab quickly. Between July 3 and July 4, 2011, the official vsftpd 2.3.4 source tarball on the project's master mirror was modified by an unknown party to include a backdoor: any login attempt with a username ending in `:)` opens a root shell on TCP 6200. The backdoor was discovered within days and the compromised tarball was removed, but copies still circulate. Metasploitable 2 ships the backdoored version on purpose.

---

## 4. Launching Metasploit Framework

```bash
msfconsole
```

`msfconsole` is Metasploit's interactive frontend. On launch it loads the module index — six thousand-plus exploit, auxiliary, post, and encoder modules in current builds — and presents a prompt.

![Metasploit Framework msfconsole running on Kali Linux.](/assets/img/blog/metasploit-storm-kit/image7.jpg)

---

## 5. Selecting and Configuring the Exploit

Inside `msfconsole`:

```
msf6 > search vsftpd
msf6 > use exploit/unix/ftp/vsftpd_234_backdoor
msf6 exploit(unix/ftp/vsft