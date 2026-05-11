---
title: "pfSense Firewall Installation and Configuration"
date: 2026-05-06 17:00:00 -0400
categories: [Network Security, Firewalls]
tags: [pfSense, Firewall, Perimeter, FreeBSD, Network Security, VMware, Lab]
description: Installing pfSense as a virtual firewall in VMware, wiring it between a NAT WAN interface and a host-only LAN, and reaching the management console from an Ubuntu client at 192.168.150.1.
image:
  path: /assets/img/blog/pfsense-firewall-install/image1.png
  alt: "Downloading the pfSense Community Edition ISO."
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
| pfSense version | Com