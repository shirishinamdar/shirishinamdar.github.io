---
title: "The Perimeter, Configured in pfSense"
date: 2026-05-06 17:00:00 -0400
categories: [Network Security, Firewalls]
tags: [pfSense, Firewall, Perimeter, FreeBSD, Network Security, VMware, Lab]
description: Installing pfSense as a virtual firewall in VMware, wiring it between a NAT WAN interface and a host-only LAN, and reaching the management console from an Ubuntu client at 192.168.150.1.
---

## Introduction

This walkthrough documents the installation and initial configuration of **pfSense**, an open-source firewall and router distribution built on FreeBSD. The exercise was performed in VMware Workstation with two virtual network adapters — a NAT adapter standing in for the WAN side, and a host-only adapter standing in for a private LAN segment. A separate Ubuntu virtual machine on the same host-only network acted as the protected client. The objective was to understand how a perimeter firewall sits between two networks, how its interfaces are assigned during install, and how to reach its web management console from inside the protected segment.

---

## Background: Why pfSense

pfSense is a FreeBSD-based platform that bundles a stateful packet filter (`pf`), a routing stack, and a web management interface into a single appliance image. It is one of the standard open-source alternatives to commercial small-and-mid-business firewalls such as SonicWall or FortiGate, and it shares most of its conceptual model with Linux-based equivalents like OPNsense, IPFire, or a stock `iptables` / `nftables` deployment.

Out of the box, pfSense provides:

- **Stateful packet filtering** — connections are tracked, so return traffic for established sessions is allowed automatically without separate inbound rules.
- **NAT and routing** — translation between WAN and LAN address spaces, port forwarding, 1:1 NAT.
- **VPN termination** — IPsec, OpenVPN, and WireGuard tunnels can be configured from the GUI.
- **VLAN support** — multiple broadcast domains over a single physical interface.
- **Add-on packages** — Snort and Suricata IDS, pfBlockerNG for threat-list-driven blocking, HAProxy, etc.
- **Traffic shaping** — bandwidth allocation and priority queueing per interface or rule.

The trade-off relative to an enterprise appliance is that everything is configured manually: there is no vendor-curated default ruleset for the threats relevant to a given industry, and no support contract behind the install. For a home lab, a small office, or a learning environment, that trade-off is usually favorable.

---

## Lab Setup

| Item | Detail |
| --- | --- |
| Hypervisor | VMware Workstation |
| pfSense version | Community Edition (CE), 2.7.x ISO from `pfsense.org` |
| VM resources | 50 GB disk, 8 GB RAM, 2 vCPU |
| Network adapter 1 (WAN) | NAT — provides upstream internet via the host |
| Network adapter 2 (LAN) | Host-only — private segment shared with the Ubuntu client |
| LAN gateway IP | `192.168.150.1` |
| Client | Ubuntu VM, attached to the same host-only segment |

The two-adapter model is the core of the lab: pfSense routes between them, and any traffic from the LAN client toward the outside world passes through the firewall.

---

## 1. Acquiring the Installer

The ISO is downloaded from the official source (`pfsense.org/download`). Recent releases ship as a `.gz`-compressed image rather than a `.rar`; in either case the archive is expanded to produce a bootable `.iso`.

![Downloading the pfSense Community Edition ISO from pfsense.org.](/assets/img/blog/pfsense-firewall-install/image1.png)

---

## 2. Creating the Virtual Machine

A new VMware Workstation virtual machine was created with the **Typical** configuration wizard, and the extracted ISO selected as the installation media.

![Selecting the pfSense ISO as the VM installation source.](/assets/img/blog/pfsense-firewall-install/image2.png)

![Naming the VM "PFsense-Fw" and choosing a guest location.](/assets/img/blog/pfsense-firewall-install/image3.png)

The VM was sized at 50 GB disk, 8 GB RAM, and 2 vCPUs — comfortably over the documented pfSense minimums but well within a typical workstation's resources.

---

## 3. Attaching Two Network Adapters

A second network adapter was added through **VM Settings → Add → Network Adapter**, then both adapters were assigned distinct connection types:

- **Adapter 1 — NAT.** Plays the role of the WAN interface and provides upstream internet via the host.
- **Adapter 2 — Host-only.** Plays the role of the LAN interface and is shared with the Ubuntu client VM so they can talk to each other on a private segment.

![Adding the second network adapter in VMware VM Settings.](/assets/img/blog/pfsense-firewall-install/image4.png)

A key detail: the Ubuntu client VM must be attached to the **same** host-only network as pfSense's Adapter 2. If the two VMs end up on different host-only segments, the firewall will be unreachable.

![Verifying Adapter 2 and the client VM share a host-only interface.](/assets/img/blog/pfsense-firewall-install/image5.png)

---

## 4. Running the Installer

The VM was powered on and booted from the ISO. The pfSense installer is a small ncurses-driven wizard — accept the license, choose the install mode (default Auto/ZFS for a single disk), confirm the target disk, and let it copy the system to the VM disk. The installer then prompts to reboot and remove the ISO from the virtual optical drive.

![pfSense installer — license acceptance screen.](/assets/img/blog/pfsense-firewall-install/image6.png)

![pfSense installer — partitioning selection.](/assets/img/blog/pfsense-firewall-install/image7.png)

![pfSense installer — file copy in progress.](/assets/img/blog/pfsense-firewall-install/image8.png)

![pfSense installer — completion and reboot prompt.](/assets/img/blog/pfsense-firewall-install/image9.png)

After reboot, pfSense presents its console menu. From this menu the interfaces (`em0`, `em1`) are mapped to logical roles: the NAT adapter becomes **WAN**, the host-only adapter becomes **LAN**, and pfSense assigns LAN an address from the default `192.168.1.0/24` range. For this lab the LAN address was reconfigured to `192.168.150.1/24` via menu option **2) Set interface(s) IP address**.

![pfSense console after first boot, showing interface assignments and IP addresses.](/assets/img/blog/pfsense-firewall-install/image10.png)

![pfSense console menu — interface IP address assignment.](/assets/img/blog/pfsense-firewall-install/image11.png)

---

## 5. Wiring Up the Client

The Ubuntu VM was attached to the same host-only network and brought up with an address on the `192.168.150.0/24` subnet. From this point any outbound traffic from the Ubuntu host transits the pfSense LAN interface.

![Configuring the Ubuntu client on the host-only network.](/assets/img/blog/pfsense-firewall-install/image12.png)

---

## 6. Reaching the Web Console

The pfSense management interface is reached over HTTPS on the LAN address:

```
https://192.168.150.1
```

The default credentials are **admin / pfsense**. On first login pfSense forces a password reset, which is the correct default — the same credential is public and identical across every fresh install on the planet, and any deployment that leaves it unchanged is one hostile DNS rebind or LAN-adjacent attacker away from full configuration takeover.

![pfSense web GUI login screen at 192.168.150.1.](/assets/img/blog/pfsense-firewall-install/image13.png)

After authenticating, pfSense presents its dashboard and a guided **Setup Wizard** that walks through hostname, timezone, WAN settings, LAN settings, and admin password change.

![pfSense dashboard after first successful login.](/assets/img/blog/pfsense-firewall-install/image14.png)

![pfSense Setup Wizard — initial configuration walkthrough.](/assets/img/blog/pfsense-firewall-install/image15.png)

![pfSense LAN configuration and default firewall rule preview.](/assets/img/blog/pfsense-firewall-install/image16.png)

The default rule set permits all LAN-initiated traffic and blocks unsolicited inbound traffic on WAN — the conventional "trust the inside, distrust the outside" posture. Everything beyond this baseline is added by hand from the **Firewall → Rules** screens.

---

## Key Observations

- The two-interface model is the entire conceptual basis of a perimeter firewall. Everything else — port forwards, VPN tunnels, IDS plugins, DNS resolvers — is layered onto that foundation.
- pfSense's default-permit-LAN posture is a usability decision, not a security one. In a hardened environment the LAN ruleset is rewritten to a default-deny stance, with explicit allow rules per service.
- Default credentials (`admin / pfsense`) are part of the documented install procedure and are recognized by every script kiddie on the internet. Any internet-exposed pfSense instance still running them has effectively no firewall. Change them before connecting anything to WAN.
- A virtual pfSense is a teaching tool, not a production posture. Hardware pfSense appliances (e.g., the official Netgate boxes) ship with cryptographic accelerators, AES-NI-capable CPUs for VPN throughput, and persistent storage tuned for write endurance — none of which a VMware VM replicates.

---

## Where This Sits in the Stack

A perimeter firewall is the first of three layers in a defense-in-depth posture. The next post in this lab series wires a **host-based firewall (UFW)** into the same Ubuntu client, so that any traffic that does make it through the perimeter also has to negotiate a second filter on the endpoint itself. Beyond that, an **intrusion detection sensor (Snort)** watches the traffic that passes both layers, and a **log aggregator (Graylog)** centralizes everything either of them emits.
