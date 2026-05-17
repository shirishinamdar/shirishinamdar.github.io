---
title: "pfSense Firewall Installation on VMware"
date: 2025-02-27 18:00:00 -0500
categories: [Network Security, Firewalls]
tags: [pfSense, Firewall, FreeBSD, VMware, Project]
description: Installing pfSense as a virtual firewall in VMware Workstation — building the VM, attaching two network adapters, running through the installer, and reaching the web GUI at 192.168.150.1 from an Ubuntu client.
image:
  path: /assets/img/blog/pfsense-firewall-install/image13.png
  alt: "pfSense web GUI login screen at 192.168.150.1."
---

pfSense is an open-source firewall and router operating system based on **FreeBSD**, designed to manage and secure network traffic. It provides features like stateful packet filtering, VPN (IPsec / OpenVPN / WireGuard), VLAN support, intrusion detection, and traffic shaping — all through a web-based interface. It can be deployed on bare-metal hardware or as a virtual machine to act as a secure gateway between internal networks and the internet.

For this project, pfSense was installed on VMware using its ISO image to build a virtual firewall that simulates a real-world network security gateway for hands-on learning and testing.

---

## Downloading the ISO

The pfSense ISO is downloaded from the official source. The download arrives as a compressed `.rar` (or `.gz` depending on the release) which is extracted to produce the bootable `.iso` file.

![Downloading the pfSense ISO from the official source.](/assets/img/blog/pfsense-firewall-install/image1.png)

---

## VMware Workstation — pfSense VM Setup

1. Create a virtual machine — **Typical** configuration.
2. Select your pfSense ISO image as the installation media.

![Selecting the pfSense ISO during VM creation.](/assets/img/blog/pfsense-firewall-install/image2.png)

3. Name your virtual machine — **PFsense-Fw**.

![Naming the VM PFsense-Fw.](/assets/img/blog/pfsense-firewall-install/image3.png)

4. Keep the disk size as **50 GB**.
5. Memory — **8 GB**.
6. Processors — **2**.
7. Add another NAT adapter.

![Adding a second network adapter in VM settings.](/assets/img/blog/pfsense-firewall-install/image4.png)

> Network Adapter 2 and the other host need to be on the **same host-only interface**, otherwise the client won't be able to reach the firewall.

![Verifying both adapters share the same host-only network.](/assets/img/blog/pfsense-firewall-install/image5.png)

---

## Installation Steps

A few installer screens to go through:

![pfSense installer — step.](/assets/img/blog/pfsense-firewall-install/image6.png)

![pfSense installer — step.](/assets/img/blog/pfsense-firewall-install/image7.png)

![pfSense installer — step.](/assets/img/blog/pfsense-firewall-install/image8.png)

![pfSense installer — step.](/assets/img/blog/pfsense-firewall-install/image9.png)

![pfSense installer — step.](/assets/img/blog/pfsense-firewall-install/image10.png)

![pfSense installer — step.](/assets/img/blog/pfsense-firewall-install/image11.png)

---

## Configuring the Client Machine

The other machine for this project is an **Ubuntu** VM set to host-only networking, which will be used as the host to configure the firewall through.

![Ubuntu client VM configured on the same host-only network.](/assets/img/blog/pfsense-firewall-install/image12.png)

---

## Reaching the pfSense GUI

To enter the GUI of pfSense, enter `192.168.150.1` in the browser URL.

![pfSense web login screen at 192.168.150.1.](/assets/img/blog/pfsense-firewall-install/image13.png)

Credentials:

- **Username:** `admin`
- **Password:** `pfsense`

![pfSense dashboard after the first login.](/assets/img/blog/pfsense-firewall-install/image14.png)

![pfSense setup wizard for the initial configuration.](/assets/img/blog/pfsense-firewall-install/image15.png)

![pfSense LAN configuration screen.](/assets/img/blog/pfsense-firewall-install/image16.png)

pfSense is now configured, and the next projects will build on this base — adding firewall rules, VPN tunnels, and more.
