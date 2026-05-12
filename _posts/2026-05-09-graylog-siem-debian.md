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

## Introduction

This walkthrough documents building a **Graylog 7.0** centralized log management and SIEM environment on a fresh Debian 12 virtual machine. The build covers each component in the stack: MongoDB 8.0 for configuration metadata, the Graylog Data Node (which bundles OpenSearch) for log storage and indexing, the Graylog Server for processing and the web UI, plus the secret and password material that ties them together securely. The objective was to understand how the pieces actually fit together rather than treating Graylog as a single opaque appliance.

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

The first command outputs a long base64 string. The second outputs a 64-character hex SHA-256 hash. Both get pasted into the config files in the next steps.

![Generated password secret and admin password hash.](/assets/img/blog/graylog-siem-debian/image5.jpg)

The admin password used during the lab was a placeholder; in any real deployment the chosen password should be long, randomly generated, and stored in a password manager. The SHA-256 here is **not** what protects the password — Graylog uses the password secret as additional material — but the same hygiene rules apply.

---

## 6. Configuring the Data Node

```bash
sudo nano /etc/graylog/datanode/datanode.conf
```

The two values to set:

```
password_secret = <paste the openssl base64 output here>
opensearch_heap = 2g
```

`opensearch_heap` is the Java heap for the embedded OpenSearch process. The standard rule of thumb is 50% of available RAM, capped at 31 GB, but for a lab VM 2 GB is plenty.

---

## 7. Configuring the Graylog Server

```bash
sudo nano /etc/graylog/server/server.conf
```

The three critical lines:

```
password_secret      = <same openssl base64 output as datanode.conf>
root_password_sha2   = <the sha256 hex from step 5>
http_bind_address    = 0.0.0.0:9000
```

`http_bind_address = 0.0.0.0:9000` makes the UI reachable from any interface — fine for a lab. In production this should be bound to a specific internal interface, and a reverse proxy with TLS termination should sit in front.

At the bottom of the file, the JVM options for the server itself:

```
GRAYLOG_SERVER_JAVA_OPTS="-Xms2g -Xmx2g -server -XX:+UseG1GC -XX:-OmitStackTraceInFastThrow"
```

`-Xms2g -Xmx2g` pins the Graylog Server heap at 2 GB. Pinning min and max equal avoids GC pauses caused by heap resizing.

![server.conf configured with password_secret, root_password_sha2, and http_bind_address.](/assets/img/blog/graylog-siem-debian/image6.jpg)

---

## 8. Starting the Services

```bash
sudo systemctl enable --now graylog-datanode
sudo systemctl enable --now graylog-server
```

The Data Node has to come up before the Server can connect to it; systemd dependency ordering handles this in the right sequence on most installs. Both should report `active (running)` within 30–60 seconds:

![Both Graylog services enabled and active.](/assets/img/blog/graylog-siem-debian/image7.jpg)

---

## 9. First-Time Setup Through the Preflight Wizard

Graylog 7.0 introduces a **preflight setup wizard** that handles initial CA generation and Data Node certificate enrollment in the browser. The one-time password to enter the wizard is printed to the server log on first start:

```bash
sudo grep -i "preflight" /var/log/graylog-server/server.log | tail -5
```

A line like `Preflight password: <password>` will appear. That password is then used in the browser at:

```
http://<server-ip>:9000
```

The wizard walks through CA creation, Data Node certificate enrollment, and admin account confirmation.

![Graylog preflight wizard in the browser.](/assets/img/blog/graylog-siem-debian/image8.jpg)

For ongoing log monitoring of the server itself:

```bash
sudo tail -f /var/log/graylog-server/server.log
```

---

## 10. Logging In and the First View

Once the preflight wizard finishes, the server transitions to the standard Graylog UI. The admin login uses the password whose SHA-256 was placed in `root_password_sha2` during step 5.

![Graylog web UI after first login.](/assets/img/blog/graylog-siem-debian/image9.jpg)

The initial view is intentionally empty — there are no streams, no inputs, and no data. The next step in any real deployment is to open **System → Inputs**, add a GELF UDP or Syslog TCP/UDP input on a chosen port, and start pointing log sources at it.

![Graylog Inputs page — adding the first log input.](/assets/img/blog/graylog-siem-debian/image10.jpg)

![Graylog overview dashboard after Data Node and Server are healthy.](/assets/img/blog/graylog-siem-debian/image11.jpg)

---

## Key Observations

- **MongoDB stores configuration; OpenSearch (Data Node) stores logs.** Confusing these two is the most common source of "where did my data go?" questions in Graylog.
- **The password secret is the single most sensitive value in the install.** Anything encrypted at rest in Graylog is keyed off it. It must match across `datanode.conf` and `server.conf`, and it should never be rotated without re-encrypting stored secrets.
- **`vm.max_map_count` is a one-line fix that produces a confusing failure when forgotten.** OpenSearch dies during startup with an obscure mmap allocation error. The sysctl change is the standard workaround on every Linux distribution.
- **The Graylog 7.0 preflight wizard replaces the old manual Elasticsearch + Mongo wiring.** This is a real ergonomic improvement; earlier versions required reading a half-dozen config files to bootstrap.
- **A SIEM with no inputs is decoration.** The install above is the *platform*. The real work — defining inputs, parsing pipelines, stream rules, alerts, and dashboards — starts after the first login. The next steps for this lab are wiring Snort alerts, UFW deny logs, and Cowrie session JSON into Graylog inputs and building cross-source dashboards.

---

## Where This Sits in the Stack

The earlier posts in this lab series each produced one source of telemetry: pfSense logs, UFW logs, Snort alerts, Tripwire integrity reports, Cowrie session data. Each one individually is useful but isolated. Graylog is what unifies them. The next post will cover plumbing those sources into Graylog inputs, defining the parsing rules that turn raw text lines into searchable fields, and writing the first alert that fires across multiple sources — for example, "Snort saw a port scan from this IP **and** UFW dropped traffic from the same IP in the same five-minute window."
