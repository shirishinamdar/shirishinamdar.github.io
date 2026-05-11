---
title: "When the File Hashes Changed"
date: 2026-05-07 11:00:00 -0400
categories: [Endpoint Security, Detection Engineering]
tags: [Tripwire, HIDS, File Integrity, Kali Linux, Detection, Lab]
description: Installing Tripwire on Kali Linux, generating site and local cryptographic keys, building a signed policy and integrity database, and confirming that an unauthorized change to /etc/passwd is detected on the next scan while an out-of-scope change in /tmp is not.
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

![Tripwire install — site key and local key passphrase confirmation.](/assets/img/blog/tripwire-hids-on-kali/image2.png)

---

## 2. Generating the Signed Configuration

The post-install layout lives under `/etc/tripwire/`. The plain-text configuration template `twcfg.txt` is converted into a signed binary `tw.cfg` using `twadmin`:

```bash
cd /etc/tripwire
sudo twadmin -m F -c tw.cfg -S site.key twcfg.txt
```

The site passphrase (`abcd` in this lab) is required to sign the configuration. After this command the binary `tw.cfg` carries a signature that pins it to the site key — any later edit of `tw.cfg` without the site key invalidates the signature and Tripwire will refuse to run.

![Generating the signed Tripwire configuration with twadmin.](/assets/img/blog/tripwire-hids-on-kali/image3.png)

---

## 3. Reviewing the Policy File

The default policy template `twpol.txt` defines what Tripwire will watch. Each entry that is **not** commented out becomes a monitored path on the next policy build:

![twpol.txt — top of the default Tripwire policy template.](/assets/img/blog/tripwire-hids-on-kali/image4.png)

![twpol.txt — file rules and rule attributes (mask, severity, etc).](/assets/img/blog/tripwire-hids-on-kali/image5.png)

Each rule specifies a path and a property mask (which attributes to track: hash, perms, owner, size, mtime). On a fresh Debian/Kali install many sections refer to filesystem paths that may not exist on the host (e.g., `/usr/sbin/rmt`, certain `init.d` scripts). For a production deployment those references are either left in place — Tripwire will warn about them but otherwise continue — or pruned to the actual filesystem.

---

## 4. Building the Policy Binary

The reviewed `twpol.txt` is then compiled into a signed binary policy `tw.pol`:

```bash
sudo twadmin --create-polfile \
    --cfgfile ./tw.cfg \
    --site-keyfile ./site.key \
    ./twpol.txt
```

Like the config file, the policy is signed with the site key. From this point forward, integrity checks reference `tw.pol` rather than the source `twpol.txt`.

![Generating the signed Tripwire policy binary.](/assets/img/blog/tripwire-hids-on-kali/image6.png)

---

## 5. Initializing the Integrity Database

The first true scan is the **baseline**. Tripwire walks every path covered by the policy, hashes file content, records the permissions and ownership of each entry, and writes the signed snapshot to `tw.db`:

```bash
sudo tripwire --init \
    --cfgfile  /etc/tripwire/tw.cfg \
    --polfile  /etc/tripwire/tw.pol \
    --site-keyfile  /etc/tripwire/site.key \
    --local-keyfile /etc/tripwire/ubuntu-local.key
```

The local passphrase is required because the resulting database is signed with the local key. This baseline represents the "known good" state of the host. Every subsequent integrity check compares the live filesystem against this snapshot and reports deltas.

![Tripwire baseline initialization — the integrity database being built.](/assets/img/blog/tripwire-hids-on-kali/image7.png)

---

## 6. Triggering a Detection

Two files were modified to test the detection path:

- `/etc/passwd` — explicitly covered by the default policy. Ownership was changed from `root:root` to `shirish:shirish` to simulate an unauthorized edit.
- `/tmp/VMwareDnD` — **not** covered by the default policy. Same ownership change applied, to act as a negative control.

```bash
sudo chown shirish:shirish /etc/passwd
sudo chown shirish:shirish /tmp/VMwareDnD
```

![Ownership change applied to /etc/passwd.](/assets/img/blog/tripwire-hids-on-kali/image8.png)

---

## 7. Running the Integrity Check

```bash
sudo tripwire --check
```

Tripwire walks the policy, re-hashes the watched paths, and produces a human-readable report. The report enumerates every deviation between the live state and the baseline, grouped by severity.

![Tripwire integrity check report — summary section.](/assets/img/blog/tripwire-hids-on-kali/image9.png)

![Tripwire integrity check report — /etc/passwd modification recorded; /tmp file absent.](/assets/img/blog/tripwire-hids-on-kali/image10.png)

The report confirmed exactly what the policy promised: the change to `/etc/passwd` appeared as a *Modified* entry, and the change to `/tmp/VMwareDnD` did not, because `/tmp` was not in the watch list.

---

## Key Observations

- A HIDS produces signal only for the paths in its policy. The defensive value of Tripwire is therefore proportional to how carefully the policy is reviewed against the actual production filesystem.
- Both signing keys are essential. An integrity tool that an attacker can rewrite from inside the host they compromised is a checkbox, not a control. Site and local passphrases belong in a password manager (or sealed offline), never on the monitored host.
- Lengthy default policies often emit large numbers of "missing path" warnings on a fresh install. These are not failures; they are reminders that the policy template targets a generic distro and should be tuned to the host.
- Tripwire detects state, not intent. A legitimate package upgrade will look identical to an attacker swapping a binary. Operational discipline therefore requires a workflow that updates the baseline after every authorized change, otherwise the next scan generates noise that drowns the real signal.

---

## Where This Sits in the Stack

A network firewall such as **pfSense** filters what enters and leaves the perimeter; a network IDS such as **Snort** watches the traffic that does pass; a host-based IDS such as Tripwire is the third layer — it watches the filesystem state of the protected endpoints themselves. Together those three layers form the classic defense-in-depth posture: stop what you can, detect what you cannot stop, and notice when something has already changed. Subsequent posts in this lab series cover the missing pieces: the host-based firewall (UFW), the deception layer (Cowrie honeypot), and the log aggregator (Graylog) that ties them all together.
