---
title: "Building a Beginner-Friendly Velociraptor Detection Lab on a Single Linux VM"
date: 2026-09-27 18:00:00 -0500
categories: [Detection Engineering, Incident Response]
tags: [Velociraptor, DFIR, Endpoint Detection, Persistence, Cron, systemd, MITRE ATT&CK, Linux, vSOC, Project]
description: A repeatable single-VM Velociraptor lab, capturing a clean baseline with five Linux artifacts, planting five harmless attacker behaviours (cron, hidden script, rogue account, malicious service, backdoor listener), and finding every one by diffing the re-collected artifacts. Includes the MITRE ATT&CK mapping and a clean-up routine.
image:
  path: /assets/img/blog/velociraptor-detection-lab/image9.png
  alt: "Velociraptor Linux.Sys.Users results with the planted backup_svc account highlighted."
---

This is a beginner-friendly **Velociraptor** detection lab on a single virtual machine, built as a foundation for the vSOC we are putting together, and written so anyone on the team can repeat it end to end.

## What is Velociraptor?

Velociraptor is a free, open-source tool for investigating computers during a security incident. It takes a live snapshot of what a machine is doing (running programs, scheduled jobs, user accounts, network connections) and lets you **compare snapshots** to spot anything new.

Instead of real malware, we plant a few harmless changes ourselves and then hunt them down. The detection steps are identical to a real incident, with none of the risk.

**The loop:** capture a clean baseline → simulate attacker activity → re-collect → diff → clean up.

---

## Step 1: Build the VM and Install Velociraptor

Create a Linux VM (Ubuntu or Mint, 2 vCPU, 2 GB RAM) and update the system.

```bash
sudo apt update && sudo apt upgrade
```

![System update running on the Linux Mint VM.](/assets/img/blog/velociraptor-detection-lab/image1.png)

Then pull the latest Linux binary from GitHub and make it executable.

```bash
mkdir ~/velo && cd ~/velo
URL=$(curl -s https://api.github.com/repos/Velocidex/velociraptor/releases/latest \
  | grep browser_download_url | grep -E 'linux-amd64"$' | cut -d '"' -f4)
wget -O velociraptor "$URL" && chmod +x velociraptor
```

![Downloading the latest Velociraptor Linux binary (v0.77.2).](/assets/img/blog/velociraptor-detection-lab/image2.png)

---

## Step 2: Launch All-in-One Mode

Start the combined server, local client, and GUI on this one box. Leave the terminal running for the session.

```bash
./velociraptor gui
```

The GUI opens at `https://127.0.0.1:8889` and the login credentials print in the terminal. Accept the self-signed certificate warning.

![The Velociraptor welcome screen after logging in as admin.](/assets/img/blog/velociraptor-detection-lab/image3.png)

Your machine appears under **Search → show all clients** within seconds.

![The local client (osboxes) connected, with its Client ID, OS, hostname and MAC address.](/assets/img/blog/velociraptor-detection-lab/image4.png)

---

## Step 3: Capture a Clean Baseline

Select your client and collect each of the artifacts below, saving the results. You will detect against them after the simulation.

| Artifact | What it captures |
|---|---|
| `Linux.Sys.Pslist` | Running processes |
| `Linux.Sys.Crontab` | Cron jobs |
| `Linux.Sys.Services` | systemd services |
| `Linux.Sys.Users` | Local user accounts |
| `Linux.Network.Netstat` | Listening sockets and connections |

Click the **+ (New Collection)** button, choose the artifact, and run it.

![The flows list with the Collected tab and the + New Collection button.](/assets/img/blog/velociraptor-detection-lab/image5.png)

![New Collection wizard, selecting an artifact to collect.](/assets/img/blog/velociraptor-detection-lab/image6.png)

Once all five have run, the baseline is complete.

![The five baseline flows collected: Pslist, Crontab, Services, Users, and Netstat.](/assets/img/blog/velociraptor-detection-lab/image8.png)

> Take a VM snapshot at this point. It makes clean-up a single click later.
{: .prompt-tip }

---

## Step 4: Simulate Attacker Activity

Run these harmless commands to plant five things a real intruder would leave behind. Each is benign and fully reversible. **Note the time before you start.**

**1. Persistence via cron** (emulates `T1053.003`):

```bash
(crontab -l 2>/dev/null; echo '* * * * * /tmp/.update.sh') | crontab -
```

![Adding the cron entry that calls /tmp/.update.sh every minute.](/assets/img/blog/velociraptor-detection-lab/image7.png)

**2. A hidden dropped script in `/tmp`** (emulates `T1564.001`):

```bash
printf '#!/bin/bash\necho beacon\n' > /tmp/.update.sh && chmod +x /tmp/.update.sh
```

**3. A rogue local account** (emulates `T1136.001`):

```bash
sudo useradd -M -s /bin/bash backup_svc
```

**4. A malicious systemd service** (emulates `T1543.002`):

```bash
sudo bash -c 'cat > /etc/systemd/system/rogue.service' <<'EOL'
[Unit]
Description=System Update Helper
[Service]
ExecStart=/tmp/.update.sh
[Install]
WantedBy=multi-user.target
EOL
sudo systemctl daemon-reload && sudo systemctl enable rogue.service
```

**5. A backdoor listener on an odd port** (emulates a C2 backdoor):

```bash
nohup nc -lk 4444 >/dev/null 2>&1 &
```

---

## Step 5: Detection

Re-run the same five artifacts from Step 3 and compare each against the baseline. You should find, in order:

| Artifact | What changed |
|---|---|
| `Linux.Sys.Crontab` | The new `* * * * *` job calling `/tmp/.update.sh` |
| `Linux.Sys.Pslist` / file listing | The hidden `.update.sh` in `/tmp` |
| `Linux.Sys.Users` | The `backup_svc` account that was not in the baseline |
| `Linux.Sys.Services` | `rogue.service` pointing at a script in `/tmp` |
| `Linux.Network.Netstat` | The process listening on port `4444` |

### The rogue account

The baseline `Linux.Sys.Users` collection returned **47** accounts, ending at `osboxes`.

![Baseline Linux.Sys.Users, 47 rows with no backup_svc.](/assets/img/blog/velociraptor-detection-lab/image10.png)

After the simulation the same artifact returned **48**, with `backup_svc` (UID 1001, home `/home/backup_svc`, shell `/bin/bash`) as the new row.

![Post-simulation Linux.Sys.Users, 48 rows with backup_svc highlighted.](/assets/img/blog/velociraptor-detection-lab/image9.png)

A quick tell: the row counts alone changed from 47 to 48, before you even read a single account name.

### The backdoor listener

`Linux.Network.Netstat` shows a **Listening** socket on `0.0.0.0:4444`, owned by `nc` with the command line `nc -lk 4444`.

![Netstat results showing nc listening on port 4444.](/assets/img/blog/velociraptor-detection-lab/image11.png)

---

## Step 6: Clean Up

Revert to the clean snapshot to undo everything at once. If you did not snapshot, reverse each change manually:

```bash
crontab -r
sudo systemctl disable rogue.service && sudo rm /etc/systemd/system/rogue.service
sudo systemctl daemon-reload
sudo userdel backup_svc
rm -f /tmp/.update.sh
pkill -f 'nc -lk 4444'
```

![Clean-up commands, removing the service and terminating the nc listener.](/assets/img/blog/velociraptor-detection-lab/image12.png)

---

## Why This Matters for a vSOC

In the vSOC we are building, this same loop is how detection works in practice:

1. **Record** what a clean endpoint looks like.
2. **Check** the endpoints, using tools like Velociraptor and Wazuh, for anything new or unusual.
3. **Turn each confirmed finding into a detection rule** that catches it automatically next time.

## MITRE ATT&CK Mapping

| Planted behaviour | Technique |
|---|---|
| Cron persistence | `T1053.003` Scheduled Task/Job: Cron |
| Hidden script in `/tmp` | `T1564.001` Hide Artifacts: Hidden Files and Directories |
| Rogue local account | `T1136.001` Create Account: Local Account |
| Malicious systemd service | `T1543.002` Create or Modify System Process: Systemd Service |
