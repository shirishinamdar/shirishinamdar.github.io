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

The most useful thing about honeypots is they tell you what attackers are trying *right now*, not what threat reports say they tried last year. Cowrie is a medium-interaction SSH and Telnet honeypot that fakes a Linux shell convincingly enough to keep an attacker typing — while it logs every keystroke, every uploaded file, and every credential pair they bothered to test.

This post is my walkthrough of standing Cowrie up in a Docker container on Kali Linux, exposing it on port 2222, and watching the session log fill up as a test client probes the fake filesystem.

> Deception systems should be reachable only by traffic you control or expect. Exposing a honeypot directly to the public internet without sufficient isolation can attract unwanted attention, fill disks rapidly, and — depending on jurisdiction and configuration — create legal complications around evidence handling and unauthorized-access definitions.

---

## Background: What Cowrie Actually Is

Honeypots fall on a spectrum of **interaction depth**:

| Type | Behavior | Trade-off |
| --- | --- | --- |
| **Low-interaction** | Emulates only the protocol handshake; never lets the attacker log in. | Cheap to run, narrow data. Mostly counts who's knocking. |
| **Medium-interaction** | Simulates a shell and filesystem; logs each command but does not execute it. | Captures attacker tools, scripts, and goals without giving them a real host. **Cowrie sits here.** |
| **High-interaction** | A real (sandboxed) operating system that actually executes attacker commands. | Richest data, highest operational risk; requires aggressive isolation. |

Cowrie speaks both **SSH** and **Telnet**, presents a configurable fake filesystem (`/etc/passwd`, `/etc/shadow`, common binaries — all forgeries), accepts a chosen password set, and logs every byte of the post-authentication session. Its outputs include per-session JSON logs, raw command transcripts, and copies of any file the a