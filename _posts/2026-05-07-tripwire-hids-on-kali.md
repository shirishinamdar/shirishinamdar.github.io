---
title: "Tripwire HIDS: File Integrity Monitoring on Linux"
date: 2026-05-07 11:00:00 -0400
categories: [Endpoint Security, Detection Engineering]
tags: [Tripwire, HIDS, File Integrity, Kali Linux, Detection, Lab]
description: Installing Tripwire on Kali Linux, generating site and local cryptographic keys, building a signed policy and integrity database, and confirming that an unauthorized change to /etc/passwd is detected on the next scan while an out-of-scope change in /tmp is not.
image:
  path: /assets/img/blog/tripwire-hids-on-kali/cover.svg
  alt: "TRIPWIRE — File Integrity Monitoring · HIDS"
---

## Introduction

This walkthrough documents the installation and first integrity check of **Tripwire**, an open-source host-based intrusion detection system (HIDS) for Linux. The exercise was performed on a Kali Linux virtual machine. The objective was to understand how a file integrity monitor builds a baseline snapshot of a filesystem, how that baseline is protected from the same attacker the tool is meant to catch, and how the daily check loop distinguishes monitored paths from unmonitored ones.

---

## Background: What Tripwire Actually Does

A host-based intrusion detection system works at the endpoint, not the network. Tripwire specifically watches the **state of files on disk** — their content, permissions, ownership, timestamps, and hashes — against a previously captured snapshot. If a file changes, the next scan reports the change. If an attacker modifies `/etc/passwd` to add a UID 0 account, or replaces `/bin/login` with a trojanized copy, or drops a webshell into `/var/www`, Tripwire flags it on the next run.

The conceptual model has four artifacts:

| Artifact | Purpose |
| --- | --- |
| **Site key** | Cryptographic key that signs the configuration and policy files. Without it, an attacker could rewrite the policy to exclude the files they tampered with. |
| **Local key** | Cryptographic key that signs the database itself. Without it, an attacker could rewrite the baseline to "match" their modified files. |
| **Policy file** (`tw.pol`) | Defines which paths are watched and which attributes (hash, ownership, perms, size, mtime) are tracked for each. |
| **Database** (`tw.db`) | The signed baseline — the snapshot of "known good" state. Every integrity check compares the live filesystem against this. |

The two passphrases protect against the most common HIDS bypass: an attacker who tries to "rewrite the rules" after compromising the host. If both keys live only in the administrator's head, the policy and the baseline both stay trustworthy even on a fully compromised host.

---

## Lab Setup

| Item | Detail |
| --- | --- |
| Host OS | Kali Linux (rolling) |
| Package source | Default Kali apt repository |
| Site passphrase | `abcd` (lab only — never use a 4-character passphrase in production) |
| Local passphrase | `1234` (same caveat) |
| Test file under policy | `/etc/passwd` |
| Test file outside policy | `/tmp/VMwareDnD` |
| Test user (to trigger ownership change) | `shirish` |

The two passphrases used here are deliberately weak so the install can be reproduced quickly. In a real deployment they should be long, randomly generated, and stored only in a sealed password manager.

---

## 1. Installing Tripwire

```bash
sudo apt-get install tripwire
```

During the install the package prompts for both the site passphrase and the local passphrase. Each phrase is requested twice for confirmation.

![Tripwire install — initial debconf passphrase prompts.](/assets/img/blog/tripwire-hids-on-kali/image1.png)

![Tripwire install — site key and local key passphrase confirmation.](/assets/img/blog/tripwire-hids-o