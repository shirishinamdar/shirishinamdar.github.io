---
title: "Apache HTTP Server with VirtualHost on Ubuntu"
date: 2026-05-10 18:54:00 -0400
categories: [Web, System Administration]
tags: [Apache, VirtualHost, Ubuntu, Web Server, Lab]
description: Installing Apache HTTP Server on Ubuntu, creating a custom document root, writing an HTML page, and configuring a name-based VirtualHost so a single server hosts multiple sites on the same IP.
image:
  path: /assets/img/blog/apache-virtualhost-ubuntu/image1.png
  alt: "Default Apache welcome page after installation on Ubuntu."
---

Two websites on one server, on one IP, on one port. The mechanism — name-based virtual hosting — has been quietly powering most of the web since the late 1990s, and Apache implements it in maybe twenty lines of configuration.

Here's my walkthrough of getting Apache up and running on Ubuntu, serving a custom HTML page from `/var/www/gci/`, and configuring a VirtualHost so requests for a specific hostname land on the new site while everything else falls through to the default Apache page.

---

## Background: How Name-Based VirtualHost Works

Apache can host more than one website on a single IP address by using the **HTTP `Host` header** the client sends with every request. The flow is:

1. Browser opens a TCP connection to the server's IP on port 80 (or 443).
2. Browser sends `GET / HTTP/1.1` plus `Host: example.com`.
3. Apache reads the `Host` header, walks its list of loaded VirtualHosts, and picks the one whose `ServerName` (or `ServerAlias`) matches.
4. Apache serves files from that VirtualHost's `DocumentRoot`.

This is called **name-based virtual hosting**. The alternative — IP-based virtual hosting — uses a different IP per site and is mostly obsolete now that public IPv4 addresses are scarce.

The minimum directives a VirtualHost needs are three:

| Directive | Purpose |
| --- | --- |
| `ServerName` | The domain name that matches the request's `Host` header. |
| `DocumentRoot` | Where the files for this site live on disk. |
| `ServerAdmin` | Email address shown in Apache's default error pages. |

---

## Lab Setup

| Item | Detail |
| --- | --- |
| Host OS | Ubuntu (any current LTS) |
| Web server | Apache 2.4 (Ubuntu's `apache2` package) |
| Default site | `/var/www/html` (untouched) |
| New site directory | `/var/www/gci/` |
| New site hostname | `gci.example.local` (mapped via `/etc/hosts`) |
| Test client | Same host, browser on the desktop |

For local testing the new hostname is faked through `/etc/hosts` rather than a real DNS record, so traffic stays inside the lab.

---

## 1. Installing Apache

```bash
sudo apt update
sudo apt install apache2 -y
```

`apt` resolves dependencies and starts the `apache2` systemd unit at the end of the install. The first verification is to open a browser at the server's IP address (find it with `ip addr` or `ifconfig`) — Apache's stock welcome page should load.

![Default Apache "It works!" welcome page in the browser.](/assets/img/blog/apache-virtualhost-ubuntu/image1.png)

The service can be inspected at any time with:

```bash
sudo systemctl status apache2
```

![systemctl status apache2 showing the service active and enabled.](/assets/img/blog/apache-virtualhost-ubuntu/image2.png)

---

## 2. Creating a New Document Root

Apache's default site serves from `/var/www/html`. Rather than overwrite that, a separate directory is created for the new site so both can coexist:

```bash
sudo mkdir /var/www/gci/
cd /var/www/gci/
sudo nano index.html
```

A minimal HTML page is written to `index.html`:

```html
<html>
  <head>
    <title>GCI Lab Site</title>
  </head>
  <body>
    <p>I'm running this website on an Ubuntu server.</p>
  </body>
</html>
```

![index.html being authored in nano under /var/www/gci/.](/assets/img/blog/apache-virtualhost-ubuntu/image3.png)

---

## 3. Writing the VirtualHost Configuration

Apache's available site configurations live in `/etc/apache2/sites-available/`. The standard pattern is to copy the default and edit, rather than write from scratch:

```bash
cd /etc/apache2/sites-available/
sudo cp 000-default.conf gci.conf
sudo nano gci.conf
```

Three directives are added or changed:

```apache
<VirtualHost *:80>
    ServerAdmin admin@example.local
    ServerName  gci.example.local
    DocumentRoot /var/www/gci/

    ErrorLog  ${APACHE_LOG_DIR}/gci-error.log
    CustomLog ${APACHE_LOG_DIR}/gci-access.log combined
</VirtualHost>
```

- `ServerAdmin` is the contact email Apache embeds in default error pages.
- `ServerName` is the hostname Apache matches against the incoming `Host` header.
- `DocumentRoot` is the on-disk path served as `/` for this site.

Per-site `ErrorLog` and `CustomLog` directives are not strictly required — without them Apache logs to the shared `error.log` and `access.log` — but separating logs per VirtualHost is much friendlier when you have to investigate a single site.

![gci.conf VirtualHost with ServerAdmin, DocumentRoot, and ServerName configured.](/assets/img/blog/apache-virtualhost-ubuntu/image4.png)

---

## 4. Enabling the Site and Reloading

```bash
sudo a2ensite gci.conf
sudo systemctl reload apach