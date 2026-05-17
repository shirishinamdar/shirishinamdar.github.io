---
title: "Cowrie SSH Honeypot Setup with Docker"
date: 2025-01-30 18:00:00 -0500
categories: [Deception, Honeypots]
tags: [Cowrie, SSH Honeypot, Docker, Kali Linux, Lab]
description: Standing up Cowrie — a medium-interaction SSH and Telnet honeypot — in a Docker container on Kali Linux, connecting to it as a test client, and watching the fake-shell session get logged.
image:
  path: /assets/img/blog/cowrie-ssh-honeypot/image4.png
  alt: "Cowrie honeypot ready to accept SSH connections on port 2222."
---

[Cowrie](https://github.com/cowrie/cowrie) is a medium-interaction SSH and Telnet honeypot. It's designed to log brute-force login attempts and shell interaction by attackers — by presenting a fake filesystem and a fake shell environment, it captures what the attacker tries to do without ever giving them a real host to do it on.

This post is the walkthrough of getting it running on a Kali VM with Docker, connecting to it as a test client, and watching the session log fill up.

---

## Setup

Started with a Kali Linux VM and installed the dependencies Docker needs.

The actual launch command for Cowrie is a single line:

```bash
docker run -p 2222:2222 cowrie/cowrie:latest
```

The `-p 2222:2222` flag maps the host's port 2222 to the container's port 2222, so any SSH or Telnet connection that lands on the host's 2222 reaches the honeypot inside the container.

![Running the Cowrie container with docker run.](/assets/img/blog/cowrie-ssh-honeypot/image2.png)

Since the Cowrie image isn't present locally, Docker pulls the layers from the registry on first run.

![Docker downloading the Cowrie image layers.](/assets/img/blog/cowrie-ssh-honeypot/image3.png)

When it finishes, the container prints **"Ready to accept SSH connections"** on port 2222 and waits.

![Cowrie ready to accept SSH connections on port 2222.](/assets/img/blog/cowrie-ssh-honeypot/image4.png)

---

## Connecting to the Honeypot

A test SSH connection from the same machine:

```bash
ssh -p 2222 root@localhost
```

Cowrie accepts the credentials and drops the client into a fake shell that looks like a normal Linux prompt.

![Successful SSH login to the Cowrie fake shell.](/assets/img/blog/cowrie-ssh-honeypot/image5.png)

To see how the deception holds up, the next command was `cat passwd` — trying to read what looks like the system's account file. Cowrie returns a fake `/etc/passwd` containing realistic-looking but fabricated user data, keeping the session going.

![Cowrie serving a fake /etc/passwd in response to the attacker's command.](/assets/img/blog/cowrie-ssh-honeypot/image6.png)

---

## Logging and Monitoring

While the fake session is going on the client side, the backend terminal where Cowrie is running shows the session in real time.

![Cowrie real-time session log on the backend terminal.](/assets/img/blog/cowrie-ssh-honeypot/image7.png)

Every command entered by the attacker — `ls`, `cd`, `cat passwd`, all of them — is timestamped and logged by Cowrie. That's the whole point of the tool: the attacker thinks they're poking around a real shell, while Cowrie quietly records what they're trying and what they're after.
