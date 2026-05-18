---
title: "Network-Based Intrusion Detection System (Snort) on Kali Linux"
date: 2025-02-14 18:00:00 -0500
categories: [Network Security, Detection Engineering]
tags: [Snort, NIDS, Kali Linux, IDS, Project]
description: Installing Snort on Kali Linux, putting the interface in promiscuous mode, writing a custom ICMP alert rule and a SYN port-scan rule, and confirming the alerts fire end to end.
image:
  path: /assets/img/blog/snort-nids-on-kali/image6.png
  alt: "Snort generating an alert on the console for a detected ping."
---

Snort is a network-based Intrusion Detection System (NIDS) used to monitor network traffic in real time and detect malicious activity such as port scans, brute-force attempts, malware communication, and policy violations. Snort operates by capturing packets, decoding protocols, applying preprocessing, and evaluating traffic against defined detection rules.

This walkthrough covers the install and configuration on a Kali Linux VM, plus a couple of custom rules to confirm the detection pipeline works.

---

## Snort Deployment and Configuration

### Environment Setup

- Started with a Kali Linux virtual machine
- Network interface configured to monitor traffic from the project network

### Installation and Initial Configuration

**1. Install Snort**

```bash
sudo apt-get install snort -y
```

**2. The network interface was configured in promiscuous mode, `192.168.147.131/24`.**

![Snort install and interface configuration.](/assets/img/blog/snort-nids-on-kali/image1.png)

```bash
sudo ip link set eth0 promisc on
```

This puts the network interface **eth0** into **promiscuous mode**.

When promiscuous mode is enabled, **eth0 will accept all network packets it sees**, not just packets that are:

- Addressed to its own MAC address
- Broadcast packets
- Multicast packets

**3. Edit configuration file**

```bash
sudo nano /etc/snort/snort.conf
```

The `HOME_NET` variable was modified to reflect the protected subnet (`192.168.147.0/24`).

![HOME_NET in snort.conf set to the protected subnet.](/assets/img/blog/snort-nids-on-kali/image2.png)

---

## Snort Rules

Snort rules define the action to take when traffic matches the rule.

**Structure:** Action Protocol Source → Destination (Options)

**Action, Defines what Snort should do when traffic matches.** Common actions:

1. **alert**, Generate alert
2. **log**, Log packet
3. **pass**, Ignore traffic
4. **drop**, Drop packet (IPS mode)
5. **reject**, Drop + notify sender

**Protocol, Specifies traffic type:** `tcp`, `udp`, `icmp`, `ip`.

**Rule: any ICMP packet sent from anywhere to your internal network:**

```
alert icmp any any -> $HOME_NET any (msg:"Ping Detected!"; sid:100001; rev:1;)
```

**Breakdown:**

- `alert`, Generate an alert when rule matches.
- `icmp`, Apply rule to ICMP traffic.
- `any any`, Match any **source IP** and any **source port**.
- `->`, Traffic flowing toward destination.
- `$HOME_NET any`, Destination must be inside protected internal network (any port).
- `(msg:"Ping Detected!"; sid:100001; rev:1;)`
    - `msg`, Alert message shown in logs.
    - `sid:100001`, Unique Snort ID (custom rule range usually starts above 100000).
    - `rev:1`, First revision of this rule.

---

## Custom Rules File

The local rules file was modified to include custom detection rules.

```bash
sudo nano /etc/snort/rules/local.rules
```

This file was used to define custom detection rules.

![local.rules with the custom ICMP detection rule.](/assets/img/blog/snort-nids-on-kali/image3.png)

Start Snort with the configuration:

```bash
sudo snort -q -l /var/log/snort -i ens33 -A console -c /etc/snort/snort.conf
```

![Snort started, listening on ens33 with console alerts.](/assets/img/blog/snort-nids-on-kali/image4.png)

This command starts Snort to monitor live network traffic on `ens33`, apply detection rules from the configuration file, display alerts on the screen, and log them to `/var/log/snort`.

To do this we need any different machine to ping to this virtual Ubuntu machine.

![Pinging the Snort host from a second machine.](/assets/img/blog/snort-nids-on-kali/image5.png)

![Snort generating the "Ping Detected!" alert on the console.](/assets/img/blog/snort-nids-on-kali/image6.png)

**The alert was successfully generated, confirming proper rule functionality.**

---

## Port Scan Detected

An additional demonstration of port scan detection was conducted using the Kali system (`192.168.147.131`) to perform an Nmap scan against the Ubuntu host (`192.168.147.130`), where the Snort NIDS was actively monitoring network traffic. The following rule was added to the Snort configuration to detect repeated SYN packets indicative of reconnaissance activity:

```
alert tcp any any -> $HOME_NET any (flags:S; threshold:type threshold, track by_src, count 5, seconds 10; msg:"Possible Port Scan Detected"; sid:100002; rev:1;)
```

Once the rule was applied and Snort was restarted, the system successfully generated alerts upon detecting the scan, confirming effective port scan detection within the project environment.

![Snort port-scan alert generated by the Nmap scan.](/assets/img/blog/snort-nids-on-kali/image7.png)
