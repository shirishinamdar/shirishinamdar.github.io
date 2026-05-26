---
title: "Building a Simple Python Port Scanner with the socket Module"
date: 2024-11-25 18:00:00 -0500
categories: [Network Security, Python]
tags: [Port Scanning, Python, socket, Nmap, Network Security, SIEM, Detection, Project]
description: A short introduction to writing a port scanner in Python using the socket module, why port scanning matters from both defensive and offensive sides, a line by line walkthrough of the code, a SIEM rule for detecting port scan activity, and safer ways to practice.
---

This is the talk I gave to Prof. Ryan's ITP150 morning and afternoon sections, written up as a post. It is a short introduction to port scanning, a complete working Python scanner using only the standard library, a line by line walkthrough of the code, the SIEM detection logic for catching port scans on the defender side, and where to practice this safely.

---

## What Are Ports?

Ports are communication endpoints on a network host. A few you see every day:

- Port 20: FTP data
- Port 22: SSH
- Port 25: SMTP
- Port 53: DNS
- Port 80: HTTP
- Port 139: NetBIOS
- Port 445: SMB file sharing on Windows

A port can be **open** (a service is listening) or **closed** (nothing accepts connections there).

---

## Why Scan Ports?

The same scan is useful to both sides.

**Defender:** identify active services, detect misconfigurations, find unnecessary open ports, troubleshoot connectivity. Ethical hackers port scan to find exposed services and entry points before real attackers do.

**Attacker:** locate open services to break into, HTTP, RDP, SSH and so on. From the responses an attacker can also fingerprint the OS type, service versions, and the applications running behind the port.

That symmetry is why detection (more on this below) matters.

---

## The Code

```python
import socket

ip = '45.33.32.156'

port_list = [20, 80, 25, 22, 53, 139]

for port in port_list:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = s.connect_ex((ip, port))

    if result == 0:
        print('Port: ', port, 'open')
    else:
        print('Port: ', port, 'closed')
```

That is the whole scanner. Standard library only, no third party packages.

---

## Line by Line

**`import socket`**, the standard library module that gives Python its networking primitives.

**`ip = '45.33.32.156'`**, the target. This particular address is `scanme.nmap.org`, an IP Nmap maintains specifically so people can practice port scanning legally. See [nmap.org](https://nmap.org/) for the rules of engagement.

**`port_list = [20, 80, 25, 22, 53, 139]`**, the ports we want to check. These are common ones worth scanning first; you can add or remove as needed.

**`for port in port_list:`**, process each port one by one.

**`s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)`**, create a new socket. `AF_INET` means IPv4, `SOCK_STREAM` means TCP.

**`result = s.connect_ex((ip, port))`**, attempt a TCP connection. `connect_ex` returns 0 on success and an error code on failure, so it never raises an exception, which is convenient for a scanner.

**`if result == 0:`**, 0 means the port accepted the connection, so it is open. Any other value means it is closed or filtered.

The output prints one line per port stating whether it is open or closed.

---

## Real World Use Cases

- Security testing on hosts and networks you own or are authorized to test.
- Troubleshooting connectivity ("is the service actually listening?").
- Firewall validation, confirming that rules block what you think they block.
- Service monitoring, watching for unexpected ports appearing on a host.

---

## Catching Port Scans on the SIEM Side

A port scan looks distinctive in logs. One source IP hits many destination ports on the same destination IP in a short window. That is the detection signature.

Here is the rule logic I use:

```
Rule Name: Port scan detected
Description: Detect port scanning activity. The rule triggers when 100 ports
             are scanned from the same source IP towards the same destination IP.

Trigger criteria:
  AND when the domain is one of the following domain names
  AND when the event(s) are detected by one or more of the listed log sources
  AND when the event context is Local to Local, or Local to Remote
  AND when at least 100 events are seen with the same Source IP,
      same Destination IP, and different Destination Port within 5 minutes
```

Tune the threshold and the window to your environment. A noisy network with vulnerability scanners running on a schedule will need allowlists for the scanner sources, otherwise the rule fires constantly on legitimate activity.

---

## Mitigation

- **Close unnecessary ports.** If a service is not needed, disable it. The fewer ports listening, the smaller the attack surface.
- **Enforce network segmentation.** Even if someone gets in, scanning is limited to the segment they land on.
- **Use deception.** Honeypots on otherwise unused ports turn scanning activity into a high confidence detection signal.

---

## Safer Ways to Practice

- **Virtual machines and cyber ranges.** A Kali VM scanning a Metasploitable VM on an isolated host network gives you the full experience with no legal exposure. Cyber Range platforms offer the same in a browser.
- **CTFs.** Most CTF challenges expect reconnaissance against the provided hosts and are explicit about what is in scope.
- **scanme.nmap.org.** The host used in the code above. Nmap maintains it for educational scanning, within the limits described on their site.

Do not scan random public IPs or servers without earned permission. The scan itself can be a violation depending on jurisdiction, and even when it is not, it is rude and counterproductive.
