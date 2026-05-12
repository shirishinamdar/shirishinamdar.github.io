---
title: "Snort NIDS Setup on Kali Linux"
date: 2026-05-05 17:32:00 -0400
categories: [Network Security, Detection Engineering]
tags: [Snort, NIDS, Kali Linux, IDS, Detection, Lab]
description: A hands-on Snort 2 lab on Kali Linux — putting an interface into promiscuous mode, writing a custom ICMP alert rule and a SYN-flood port-scan rule, and confirming detections fire end to end on a private virtual network.
image:
  path: /assets/img/blog/snort-nids-on-kali/image1.png
  alt: "Confirming the network interface is in promiscuous mode for Snort."
---

Every network intrusion-detection system rests on the same idea: see every packet that crosses your wire, decide which ones look suspicious, alert. Snort has been doing exactly that since 1998, and it's still one of the cleanest ways to learn what a NIDS actually does — because the rule syntax is plain text, the documentation is excellent, and the path from "install" to "first detection" takes about an hour.

Here's my walkthrough of doing that on Kali Linux: installing Snort, putting an interface into promiscuous mode, writing two custom detection rules from scratch, and confirming they fire when I poke the host with `ping` and `nmap` from a second VM.

---

## Background: What Snort Actually Does

Snort sits on a network segment and inspects every packet it can see. Internally it does four things in sequence: capture packets from a configured interface, decode protocol headers (Ethernet, IP, TCP/UDP/ICMP, application-layer), run packet preprocessors that normalize and reassemble traffic, and finally evaluate each packet against a chained ruleset. When a rule matches, Snort emits an alert to the configured output (console, syslog, unified2 log, etc).

The default deployment is passive: the interface is set to promiscuous mode, copies of traffic flow into Snort, but Snort does not interfere with the conversation. In inline (IPS) mode Snort sits between two interfaces and can drop or reject packets, but that is out of scope here.

---

## Lab Setup

| Item | Detail |
| --- | --- |
| IDS host | Kali Linux VM, interface `eth0` / `ens33` |
| Target host | Ubuntu VM on the same NAT segment |
| Network | `192.168.147.0/24` (private, isolated) |
| IDS IP | `192.168.147.131` |
| Target IP | `192.168.147.130` |
| Snort version | Snort 2.9.x (from Kali apt repository) |

---

## 1. Installing Snort

```bash
sudo apt-get install snort -y
```

The package installer prompts for a HOME_NET value; the default `any` is accepted at install time and corrected later in the config file.

---

## 2. Putting the Interface in Promiscuous Mode

```bash
sudo ip link set eth0 promisc on
```

By default a NIC discards any frame whose destination MAC address is not its own (or a broadcast/multicast it has subscribed to). Promiscuous mode disables that filter — the card hands every frame it sees up the stack, which is what an IDS requires to inspect traffic that is not addressed to itself.

![Confirming the network interface is in promiscuous mode.](/assets/img/blog/snort-nids-on-kali/image1.png)

---

## 3. Setting HOME_NET in snort.conf

```bash
sudo nano /etc/snort/snort.conf
```

The `HOME_NET` variable defines what Snort considers the protected internal network. Rules reference it as `$HOME_NET`. For this lab it was set to the local subnet:

```
ipvar HOME_NET 192.168.147.0/24
```

![Editing HOME_NET in /etc/snort/snort.conf.](/assets/img/blog/snort-nids-on-kali/image2.png)

---

## 4. Anatomy of a Snort Rule

Every Snort rule follows the same shape:

```
action protocol src_ip src_port -> dst_ip dst_port (options)
```

The action determines what Snort does on a match. The protocol restricts which packets the rule evaluates. The address/port pair on each side of the `->` defines direction. The parenthesized options carry the metadata — the alert message, the rule ID, the revision, and any pattern matchers.

| Field | Common values |
| --- | --- |
| Action | `alert` (log + emit alert), `log` (silent log), `pass` (whitelist), `drop` and `reject` (inline only) |
| Protocol | `tcp`, `udp`, `icmp`, `ip` |
| Address / port | Literal CIDR, variable like `$HOME_NET`, or `any` |
| Direction | `->` (one-way), `<>` (bidirectional) |
| Options | `msg`, `sid`, `rev`, `content`, `flags`, `threshold`, etc. |

Custom rules live in `/etc/snort/rules/local.rules`. SIDs (Snort IDs) for user-defined rules conventionally start at 1,000,000 to avoid colliding with the shared community/VRT rule space.

---

## 5. First Custom Rule: Detect Inbound Pings

```
alert icmp any any -> $HOME_NET any (msg:"Ping Detected!"; sid:100001; rev:1;)
```

Rea