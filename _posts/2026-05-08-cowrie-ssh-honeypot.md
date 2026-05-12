---
title: Cowrie SSH Honeypot Setup with Docker
date: 2026-05-08 18:54:00 -0400
categories: [Deception, Honeypots]
tags: [Cowrie, SSH Honeypot, Docker, Deception, Lab]
description: Standing up Cowrie — a medium-interaction SSH and Telnet honeypot — in a Docker container on Kali, mapping port 2222 to capture brute-force attempts, and reading the resulting session logs.
image:
  path: /assets/img/blog/cowrie-ssh-honeypot/cover.svg
  alt: "COWRIE — SSH Honeypot in Docker"
---

Cowrie , a medium-interaction SSH and Telnet honeypot designed to log
brute-force attacks and shell interaction performed by attackers. It
functions by providing a fake filesystem and shell environment, allowing
security researchers to capture malware payloads and monitor
unauthorized activity in a controlled environment.**  
**

![](/assets/img/blog/cowrie-ssh-honeypot/image1.png)**  
<https://github.com/cowrie/cowrie>  
  
Started with KALI VM and Installed necessary dependencies.  
  
$ docker run -p 2222:2222 cowrie/cowrie:latest  
**

**This command runs a Cowrie honeypot container, mapping your computer's
port 2222 to the container's port 2222 to capture and log unauthorized
SSH or Telnet access attempts.**

**  
**

**This command maps the host's port 2222 to the container's port 2222,
allowing external SSH connections to reach the honeypot
environment.**

![](/assets/img/blog/cowrie-ssh-honeypot/image2.png)

Since the Cowrie image was not found locally, Docker downloads the
necessary components to build the runtime environment.

![](/assets/img/blog/cowrie-ssh-honeypot/image3.png)

**The honeypot confirms it is "Ready to accept SSH connections" on port
2222.**

![](/assets/img/blog/cowrie-ssh-honeypot/image4.png)

A user connects via **ssh -p 2222 root@localhost** and successfully logs
in

Cowrie accepts the credentials to lure the user into a fake shell
environment.

![](/assets/img/blog/cowrie-ssh-honeypot/image5.png)

 The user attempts to view sensitive files using commands like cat
passwd.

The honeypot provides a fake /etc/passwd file containing realistic but
fabricated user data to keep the attacker engaged.

**  
**

![](/assets/img/blog/cowrie-ssh-honeypot/image6.png)

**Logging and Monitoring:**  
The backend terminal displays real-time logs of the session-

![](/assets/img/blog/cowrie-ssh-honeypot/image7.png)

Every command entered by the attacker such as ls, cd etc, and cat passwd
, is timestamped and logged by Cowrie to reveal the attacker's intent
and techniques.
