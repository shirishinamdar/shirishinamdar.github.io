---
title: Graylog SIEM Setup on Debian 12
date: 2026-05-09 18:54:00 -0400
categories: [SIEM, Log Management]
tags: [Graylog, SIEM, Debian, Log Management, Lab]
description: Installing Graylog 7.0 on Debian 12 — MongoDB, Graylog Data Node, secrets generation, web interface — to build a centralized log management and SIEM environment from scratch.
image:
  path: /assets/img/blog/graylog-siem-debian/image1.jpg
  alt: Graylog SIEM Setup on Debian 12
---

# Overview

This week's work focused on three main tasks:

  - This week focused on installing and configuring Graylog 7.0 on a
    Debian 12 virtual machine as part of building a centralized log
    management and SIEM environment.

  - Graylog was set up with MongoDB 8.0, a Graylog Data Node, and the
    Graylog Server, including secrets generation, service configuration,
    and web interface access.

  - Started Inclass hands on labs for pfsense firewall ITN 263

# Graylog Installation on Debian 12  

## What is Graylog?

Graylog is a log management and analysis platform. It collects, indexes,
and analyzes log data from various sources (servers, network devices,
applications) and presents it in a centralized, searchable interface.
Think of it as a smarter, easier-to-use ELK (Elasticsearch, Logstash,
Kibana) stack alternative.

## Core Components

Graylog Server - The brain. Processes logs, handles searches,
dashboards, alerts.

MongoDB - Stores metadata and configuration (not the logs themselves).

Elasticsearch - Stores actual log messages, enables fast search.

Graylog Web Interface - UI for searching, visualizing, and alerting on
logs.

##   
Step 1 - System Prerequisites

Updated the system and installed required packages on **Debian 12.13**.

sudo apt update && sudo apt upgrade -y

sudo apt install -y curl gnupg wget apt-transport-https

![](/assets/img/blog/graylog-siem-debian/image1.jpg)

*Figure 1 -- Debian 12.13 system after running apt update/upgrade and
installing prerequisites.*

## Step 2 - Install MongoDB 8.0

Added the MongoDB 8.0 APT repository, installed mongodb-org, and enabled
the mongod service.

curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \

sudo gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor

echo "deb \[signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg\] \

https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" | \

sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list

sudo apt update

sudo apt install -y mongodb-org

sudo systemctl enable --now mongod

sudo systemctl status mongod

![](/assets/img/blog/graylog-siem-debian/image2.jpg)

*Figure 2 -- mongod service running and enabled after MongoDB 8.0
installation.*

## Step 3 - Set vm.max_map_count

Set vm.max_map_count=262144 in sysctl -- required by the Graylog Data
Node (OpenSearch).

echo 'vm.max_map_count=262144' | sudo tee -a
/etc/sysctl.d/99-graylog-datanode.conf

sudo sysctl --system

![](/assets/img/blog/graylog-siem-debian/image3.jpg)

*Figure 3 -- sysctl configuration applied for vm.max_map_count.*

## Step 4 - Add Graylog Repo & Install Data Node + Server

Downloaded and installed the Graylog 7.0 repository package, then
installed graylog-datanode and graylog-server.

wget
https://packages.graylog2.org/repo/packages/graylog-7.0-repository_latest.deb

sudo dpkg -i graylog-7.0-repository_latest.deb

sudo apt update

sudo apt install -y graylog-datanode graylog-server

![](/assets/img/blog/graylog-siem-debian/image4.jpg)

*Figure 4 -- Graylog Data Node and Server packages being installed from
the Graylog 7.0 repository.*

## Step 5 - Generate Secrets

Generated a 96-byte base64 password secret and a SHA256 hash of the
admin password (student@NOVA).

# Password secret (used in both datanode.conf and server.conf)

openssl rand -base64 96 | tr -d '\\n'

#echo -n "student@NOVA" | sha256sum | awk '{print $1}'

![](/assets/img/blog/graylog-siem-debian/image5.jpg)

*Figure 5 -- OpenSSL-generated password secret and SHA256 admin password
hash output.*

## Step 6 - Configure Data Node

Edited datanode.conf to set the password secret and OpenSearch heap
size.

sudo nano /etc/graylog/datanode/datanode.conf

# Set:

password_secret = <output from openssl above>

opensearch_heap=2g

## Step 7 - Configure Graylog Server

Edited server.conf to set the password secret, admin password hash, and
bind address.

sudo nano /etc/graylog/server/server.conf

# Set:

password_secret = <same openssl output as above>

root_password_sha2 = <sha256 hash from Step 5>

http_bind_address = 0.0.0.0:9000

# Add at bottom:

GRAYLOG_SERVER_JAVA_OPTS="-Xms2g -Xmx2g -server -XX:+UseG1GC
-XX:-OmitStackTraceInFastThrow"

![](/assets/img/blog/graylog-siem-debian/image6.jpg)

*Figure 6 -- server.conf configured with password_secret,
root_password_sha2, and http_bind_address.*

## Step 8 - Start Services

Enabled and started both the Graylog Data Node and Server using
systemctl.

sudo systemctl enable --now graylog-datanode

sudo systemctl enable --now graylog-server

![](/assets/img/blog/graylog-siem-debian/image7.jpg)

*Figure 7 -- Graylog Data Node and Server services enabled and started
via systemctl.*

## Step 9 - Preflight Setup & Web Interface Access

Retrieved the one-time preflight password from the server log and
completed the setup wizard in the browser at
http://192.168.131.128:9000.

sudo grep -i "preflight" /var/log/graylog-server/server.log | tail -5

# Then access in browser:

http://admin:RofhxejRFp@192.168.131.128:9000

# Monitor logs:

sudo tail -50 /var/log/graylog-server/server.log

![](/assets/img/blog/graylog-siem-debian/image8.jpg)

*Figure 8 -- Graylog preflight wizard in the browser for initial CA and
Data Node setup.*

![](/assets/img/blog/graylog-siem-debian/image9.jpg)

*Figure 9 -- Graylog server log showing service startup and preflight
mode.*

![](/assets/img/blog/graylog-siem-debian/image10.jpg)

*Figure 10 -- Server log confirming Data Node provisioning progress.*

![](/assets/img/blog/graylog-siem-debian/image11.jpg)

*Figure 11 -- Graylog web interface fully loaded and ready for log
ingestion and dashboard creation.*
