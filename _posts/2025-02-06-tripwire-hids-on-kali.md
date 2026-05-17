---
title: "Host-Based IDS Tripwire Installation on Kali Linux"
date: 2025-02-06 18:00:00 -0500
categories: [Endpoint Security, Detection Engineering]
tags: [Tripwire, HIDS, File Integrity, Kali Linux, Project]
description: Installing Tripwire on Kali Linux, generating site and local keys, building a signed policy and integrity database, then triggering a detection by changing ownership of /etc/passwd.
image:
  path: /assets/img/blog/tripwire-hids-on-kali/image10.png
  alt: "Tripwire integrity check report showing /etc/passwd modification detected."
---

Tripwire is a host-based Intrusion Detection System for Linux. It monitors a Linux system to detect and report any unauthorized changes to files and directories. Once the baseline is created, Tripwire monitors and detects **which file** changed, **what** was changed, **who** changed it, and **when** it was changed. If the changes are legitimate, you can update the Tripwire database to accept them.

This project walks through installing Tripwire on a Kali Linux machine, generating the signed configuration and baseline, then deliberately changing a watched file to confirm the detection fires.

---

## 1. Install and Create Site Key and Local Passphrase

```bash
sudo apt-get install tripwire
```

![Tripwire installation in progress.](/assets/img/blog/tripwire-hids-on-kali/image1.png)

For the passphrases used in this project:

- Site key passphrase: `abcd`
- Local key passphrase: `1234`

![Setting the site key and local key passphrases during install.](/assets/img/blog/tripwire-hids-on-kali/image2.png)

---

## 2. Create Keys and Initialize Database

Move into the Tripwire config directory and generate the signed configuration:

```bash
cd /etc/tripwire
twadmin -m F -c tw.cfg -S site.key twcfg.txt
```

Enter your passphrase, which is `abcd`.

![Signed Tripwire configuration generated with twadmin.](/assets/img/blog/tripwire-hids-on-kali/image3.png)

We will also look at the **twpol.txt** configuration file here. Anything which is not commented out is in the monitoring scope.

![twpol.txt — Tripwire policy template.](/assets/img/blog/tripwire-hids-on-kali/image4.png)

![twpol.txt — more of the policy template.](/assets/img/blog/tripwire-hids-on-kali/image5.png)

Next, run the following commands to create the Tripwire policy file and the Tripwire database:

```bash
sudo twadmin --create-polfile --cfgfile ./tw.cfg --site-keyfile ./site.key ./twpol.txt
```

![Tripwire policy binary created with twadmin --create-polfile.](/assets/img/blog/tripwire-hids-on-kali/image6.png)

For the database:

```bash
sudo tripwire --init \
  --cfgfile  /etc/tripwire/tw.cfg \
  --polfile  /etc/tripwire/tw.pol \
  --site-keyfile  /etc/tripwire/site.key \
  --local-keyfile /etc/tripwire/ubuntu-local.key
```

![Tripwire integrity database being built.](/assets/img/blog/tripwire-hids-on-kali/image7.png)

This has created the Tripwire integrity database, which contains the filesystem snapshot — the baseline. It will then be used as the reference point for all file integrity verifications.

---

## 3. Run a Tripwire Filesystem Check

For observation, and as an example to test whether the policy for file integrity is working, the owner of `/etc/passwd` was changed to a newly created user `shirish`, from inside the `/etc` folder:

```bash
sudo chown shirish:shirish passwd
```

![Ownership of /etc/passwd changed to user shirish.](/assets/img/blog/tripwire-hids-on-kali/image8.png)

The same change was applied to a file in `/tmp` — which is **not** in the watch list — as a comparison:

```bash
sudo chown shirish:shirish VMwareDnD
```

Next, run a filesystem integrity check with Tripwire:

```bash
sudo tripwire --check
```

The Tripwire report shows whether any file modifications are present.

![Tripwire check — integrity report summary.](/assets/img/blog/tripwire-hids-on-kali/image9.png)

![Tripwire check — /etc/passwd flagged as modified.](/assets/img/blog/tripwire-hids-on-kali/image10.png)

We can see that our file `/etc/passwd` was modified, and it shows up in the report — but the `/tmp` file does not, because we did not enable a watchlist for that path in `twpol.txt`.
