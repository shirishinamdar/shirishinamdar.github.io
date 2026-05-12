---
title: "Graylog SIEM Setup on Debian 12"
date: 2026-05-09 18:54:00 -0400
categories: [SIEM, Log Management]
tags: [Graylog, SIEM, Debian, MongoDB, Log Management, OpenSearch, Lab]
description: Building a Graylog 7.0 SIEM from scratch on Debian 12 — MongoDB 8.0 for metadata, the Graylog Data Node (OpenSearch) for log storage, password secret and admin hash generation, service start, and first login through the preflight wizard.
image:
  path: /assets/img/blog/graylog-siem-debian/image1.jpg
  alt: "Debian 12.13 system after apt update and installing Graylog prerequisites."
---

A SIEM with no log sources is just a search engine over an empty index. The hard part of building one isn't installing the software — it's getting your firewall, your IDS, your honeypot, and your endpoint sensors all to send their telemetry to the same place in a parseable format. But you have to install the software first, so this post is about that.

Here's my walkthrough of standing up Graylog 7.0 on a fresh Debian 12 VM: MongoDB for the configuration metadata, the Graylog Data Node (which bundles OpenSearch) for the actual log storage, the Graylog Server for processing and the web UI, and the password material that ties all three together.

---

## Background: What Graylog Is

Graylog is a log management and analysis platform. It ingests structured and unstructured log data from servers, network devices, firewalls, applications, IDS/IPS sensors, and cloud services; indexes the data; and presents a unified search, alerting, and dashboarding surface for analysts. It sits in the same space as Splunk and the Elastic-based ELK / Wazuh stacks, with a deliberately narrower default install footprint.

The architecture has four components that have to be installed and configured together:

| Component | Role |
| --- | --- |
| **Graylog Server** | The brain. Processes incoming logs, runs searches, evaluates alert rules, serves the web UI. |
| **MongoDB** | Stores configuration and metadata (users, streams, dashboards, alert definitions). Does **not** store log messages. |
| **Graylog Data Node** (OpenSearch) | Stores the actual log messages and provides the search index. In Graylog 7.0, this is bundled as a managed Data Node. |
| **Web Interface** | The browser-facing UI for searching, visualizing, and managing the platform. |

A SIEM is only as useful as the sources feeding it. The install below stands up the platform itself; subsequent posts in this lab series cover wiring upstream sources (Snort alerts, UFW deny logs, Cowrie session JSON, Tripwire integrity reports) into it for correlation.

---

## Lab Setup

| Item | Detail |
| --- | --- |
| Host OS | Debian 12.13 (Bookworm) |
| Graylog version | 7.0 (Open) |
| MongoDB version | 8.0 |
| Data Node | Bundled OpenSearch (managed by Graylog Data Node service) |
| Server RAM | 4 GB minimum, 8 GB recommended for the data node + server |
| Web UI bind | `0.0.0.0:9000` (LAN-reachable for this lab) |

A 4 GB VM will complete the install but will struggle once real log ingest starts. The OpenSearch heap is sized at 2 GB and the Graylog server JVM at 2 GB in the configuration below, which is workable for a single-host lab and undersized for anything resembling production volume.

---

## 1. System Prerequisites

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl gnupg wget apt-transport-https
```

The four prerequisite packages let the system add a third-party repository over HTTPS, verify its signing key, and download release artifacts.

![Debian 12.13 after apt update/upgrade with prerequisites installed.](/assets/img/blog/graylog-siem-debian/image1.jpg)

---

## 2. Installing MongoDB 8.0

MongoDB is not in the Debian default repositories. The MongoDB project's APT repository is added with its signing key, then the `mongodb-org` meta-package is installed:

```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

echo "deb [signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg] \
  https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod
sudo systemctl status mongod
```

The `mongod` service should report `active (running)` after the final command:

![mongod running and enabled after MongoDB 8.0 install.](/assets/img/blog/graylog-siem-debian/image2.jpg)

---

## 3. Tuning the Kernel for OpenSearch

The Graylog Data Node wraps OpenSearch, which requires a larger `vm.max_map_count` than Debian's default. Without this setting, OpenSearch fails to start at memory-map allocation time:

```bash
echo 'vm.max_map_count=262144' | \
  sudo tee -a /etc/sysctl.d/99-graylog-datanode.conf

sudo sysctl --system
```

![sysctl applied — vm.max_map_count set to 262144.](/assets/img/blog/graylog-siem-debian/image3.jpg)

This change persists across reboots because it lives in `/etc/sysctl.d/`.

---

## 4. Adding the Graylog Repository and Installing Packages

Graylog publishes a repository helper as a `.deb` package. Installing it adds the apt source plus the project's signing key in one step:

```bash
wget https://packages.graylog2.org/repo/packages/graylog-7.0-repository_latest.deb
sudo dpkg -i graylog-7.0-repository_latest.deb
sudo apt update
sudo apt install -y graylog-datanode graylog-server
```

Both packages are installed but **not yet started** — they need configuration first.

![graylog-datanode and graylog-server packages installed.](/assets/img/blog/graylog-siem-debian/image4.jpg)

---

## 5. Generating Secrets

Graylog needs two secrets to start: a **password secret** (used to encrypt and salt stored credentials) and an **admin password hash** (the root web-UI login).

```bash
# 96-byte random base64 string — used in BOTH datanode.conf and server.conf
openssl rand -base64 96 | tr -d '\n'

# SHA256 of the chosen admin password
echo -n "ChooseAStrongAdminPasswordHere" | sha256sum | awk '{print $1}'
```

The first command outputs a long base64 string. The second outputs a 64-character hex SHA-256 hash. Both 