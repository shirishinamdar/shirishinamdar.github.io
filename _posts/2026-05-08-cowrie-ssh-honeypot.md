---
title: "Cowrie SSH Honeypot Setup with Docker"
date: 2026-05-08 18:54:00 -0400
categories: [Deception, Honeypots]
tags: [Cowrie, SSH Honeypot, Docker, Deception, Lab]
description: Standing up Cowrie — a medium-interaction SSH and Telnet honeypot — in a Docker container on Kali, mapping port 2222 to capture brute-force attempts, and reading the resulting session logs.
image:
  path: /assets/img/blog/cowrie-ssh-honeypot/image1.png
  alt: "Cowrie SSH honeypot — Ready to accept SSH connections on port 2222."
---

## Introduction

This walkthrough documents the deployment of **Cowrie**, a medium-interaction SSH and Telnet honeypot designed to capture brute-force login attempts and post-authentication shell interaction. The honeypot was deployed in a Docker container on a Kali Linux host, exposed on TCP port 2222 instead of the privileged port 22, and used to observe a deliberate test interaction from the same host. The objective was to understand how a deception system fakes a Unix environment convincingly enough to be useful, and what an analyst gets back from a single captured session.

> Deception systems should be reachable only by traffic you control or expect. Exposing a honeypot directly to the public internet without sufficient isolation can attract unwanted attention, fill disks rapidly, and — depending on jurisdiction and configuration — create legal complications around evidence handling and unauthorized-access definitions.

---

## Background: What Cowrie Actually Is

Honeypots fall on a spectrum of **interaction depth**:

| Type | Behavior | Trade-off |
| --- | --- | --- |
| **Low-interaction** | Emulates only the protocol handshake; never lets the attacker log in. | Cheap to run, narrow data. Mostly counts who's knocking. |
| **Medium-interaction** | Simulates a shell and filesystem; logs each command but does not execute it. | Captures attacker tools, scripts, and goals without giving them a real host. **Cowrie sits here.** |
| **High-interaction** | A real (sandboxed) operating system that actually executes attacker commands. | Richest data, highest operational risk; requires aggressive isolation. |

Cowrie speaks both **SSH** and **Telnet**, presents a configurable fake filesystem (`/etc/passwd`, `/etc/shadow`, common binaries — all forgeries), accepts a chosen password set, and logs every byte of the post-authentication session. Its outputs include per-session JSON logs, raw command transcripts, and copies of any file the attacker uploaded via `wget`, `curl`, or SCP. Source: [github.com/cowrie/cowrie](https://github.com/cowrie/cowrie).

For threat intelligence work, Cowrie is one of the standard signal sources for credential lists in active use, popular scanned ports, and small payload droppers. Larger deployments forward Cowrie's JSON output into a SIEM (covered in the Graylog post in this series) for aggregation and correlation across multiple sensors.

---

## Lab Setup

| Item | Detail |
| --- | --- |
| Host OS | Kali Linux (rolling) |
| Container runtime | Docker (community edition) |
| Image | `cowrie/cowrie:latest` (official Docker Hub image) |
| Honeypot SSH port (host) | `2222/tcp` |
| Honeypot SSH port (container) | `2222/tcp` |
| Test client | Same Kali host, loopback |

Running on port 2222 instead of 22 keeps Cowrie from clashing with the host's real SSH daemon. In a production deployment the typical pattern is to NAT or `iptables`-redirect external traffic on port 22 to the container's 2222, so attackers see a normal-looking SSH service while the host's actual administrative SSH lives on a different port behind a firewall ACL.

---

## 1. Pulling and Running the Container

The official image is pulled and started with a single `docker run`:

```bash
docker run -p 2222:2222 cowrie/cowrie:latest
```

Flag-by-flag:

- `-p 2222:2222` maps the host's TCP 2222 to the container's TCP 2222.
- The image tag `cowrie/cowrie:latest` selects the published Cowrie image on Docker Hub.

Because the image is not present locally, Docker pulls the layers from the registry on first run.

![docker run pulling the cowrie/cowrie image layers.](/assets/img/blog/cowrie-ssh-honeypot/image2.png)

![Docker layer download progress for the Cowrie image.](/assets/img/blog/cowrie-ssh-honeypot/image3.png)

---

## 2. The Honeypot Comes Up

When initialization finishes, Cowrie prints a startup banner indicating that the SSH listener is bound and ready:

```
twistd cowrie - Twisted reactor running
cowrie.ssh.factory - Ready to accept SSH connections on port 2222
```

![Cowrie ready to accept SSH connections on port 2222.](/assets/img/blog/cowrie-ssh-honeypot/image4.png)

At this point the honeypot is live. Any TCP SYN to port 2222 will be answered, and any subsequent SSH handshake will be honored with Cowrie's fake shell.

---

## 3. Simulated Attacker Connection

A test client connected from the same host to demonstrate the capture path:

```bash
ssh -p 2222 root@localhost
```

Cowrie accepts the credentials per its configured `userdb.txt` policy — by default it accepts a curated set including weak passwords like `root/root` or `root/123456` that real attackers test first. The user is then dropped into a fake interactive shell that looks like a normal Linux prompt.

![Successful SSH login to the Cowrie fake shell.](/assets/img/blog/cowrie-ssh-honeypot/image5.png)

---

## 4. Probing the Fake Filesystem

The attacker (in this case, the test client) executed `cat /etc/passwd` to enumerate accounts. Cowrie served a pre-staged fake `/etc/passwd` containing realistic-looking but entirely synthetic users — the file is part of the honeypot's deception package, **not** the host's real one.

![Cowrie returning a fake /etc/passwd in response to the attacker's command.](/assets/img/blog/cowrie-ssh-honeypot/image6.png)

This is the core of medium-interaction deception: every system call the attacker makes is answered with a plausible-looking artifact, while no real binary is invoked and nothing on the host is touched.

---

## 5. Reading the Session Logs

On the backend, Cowrie writes a structured event stream as the session unfolds. Each command executed by the client appears with a timestamp, source IP, session ID, and the raw command line:

![Cowrie real-time session log showing the attacker's commands.](/assets/img/blog/cowrie-ssh-honeypot/image7.png)

The same data is also written to `var/log/cowrie/cowrie.json` in JSON form, one event per line, which is the format that downstream SIEM pipelines (Graylog, Wazuh, Splunk) ingest directly. A single recorded session captures:

- Source IP and source port.
- Username and password attempted (with the username/password combo recorded even when authentication is allowed).
- The full sequence of commands typed.
- Any files uploaded (preserved verbatim under `var/lib/cowrie/downloads/`).
- The SSH client software string the attacker advertised.

---

## Key Observations

- **Port placement matters.** Running Cowrie on 2222 protects the host's real SSH, but real attackers expect SSH on 22. A production sensor needs an upstream redirect (iptables PREROUTING or a network device) so the honeypot sees the same scanners that target port 22 in the wild.
- **The fake filesystem is configurable.** `/etc/passwd`, `/etc/shadow`, MOTD banners, kernel version, and hostname all live in the Cowrie data files. A useful honeypot has these tuned to look like a specific target profile (e.g., a stock Ubuntu cloud image) rather than the default Cowrie defaults that some attacker scripts now fingerprint.
- **Credentials are intel.** The username/password pairs attackers actually try are valuable — they reveal which credential leaks are in active use this week. Even a single low-volume sensor produces a steady credential feed worth correlating against threat-intel sources.
- **The JSON log is the product.** Watching the terminal is satisfying once; the real value is forwarding `cowrie.json` to a SIEM where weeks of sessions can be aggregated, deduplicated by source IP, and joined to other signals.

---

## Where This Sits in the Stack

A honeypot is most useful when its output reaches the same analytical pipeline as the rest of your security telemetry. The next two posts in this lab series cover that pipeline: **UFW** as the host-based filter that controls who can reach the sensor at all, and **Graylog** as the SIEM that ingests Cowrie's JSON stream alongside other sources for correlation and dashboards.
