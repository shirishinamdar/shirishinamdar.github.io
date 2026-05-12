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

## Introduction

This walkthrough documents installing the **Apache HTTP Server** on Ubuntu, creating a custom website directory and a basic HTML page, then configuring a **name-based VirtualHost** so the same server can serve multiple sites under different domain names. The objective was to understand how Apache routes an incoming HTTP request from the wire to the correct document root, and what each of the three core directives in a VirtualHost actually controls.

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
sudo systemctl reload apache2
```

`a2ensite` creates a symlink in `/etc/apache2/sites-enabled/` pointing at the file in `sites-available/`. The reload tells Apache to re-read its configuration without dropping in-flight connections.

The two companion commands are worth knowing too:

```bash
sudo a2dissite gci.conf       # remove the symlink — site disabled
sudo apache2ctl configtest    # syntax check before reload
```

`configtest` should be run before every reload in production. A bad VirtualHost file can prevent Apache from starting at all, taking *every* site on the server down with it.

---

## 5. Faking DNS Locally

In production the hostname would resolve through a real DNS record. For a local lab, the same effect is achieved by editing `/etc/hosts` on the client:

```bash
sudo nano /etc/hosts
```

Append a line mapping the test hostname to the server's IP (for the lab, the same VM, so 127.0.0.1 or its LAN address):

```
192.168.150.50    gci.example.local
```

From this point, any request to `gci.example.local` from this machine resolves to the lab server, sends an HTTP request with the correct `Host` header, and triggers the new VirtualHost.

---

## 6. Verifying the VirtualHost Is Routing

Browsing to `http://gci.example.local/` should now load the custom `index.html`, not the default Apache welcome page:

![Custom HTML page served at gci.example.local after VirtualHost activation.](/assets/img/blog/apache-virtualhost-ubuntu/image5.png)

A second check is to request the bare IP, which should still hit the default site (because no VirtualHost claims that hostname). The split confirms the routing decision is happening on the `Host` header, not on the IP or port.

---

## Key Observations

- **The `Host` header does the routing.** A request to the same IP, same port can reach completely different document roots depending on which hostname the client sent. Spoof the `Host` header (`curl -H 'Host: gci.example.local' http://<ip>/`) and Apache will believe you.
- **The `000-default.conf` file is special.** It catches any request whose `Host` value doesn't match any defined VirtualHost. In a multi-tenant setup it's worth deciding deliberately what that file serves — a stub page, a 404, or a redirect.
- **`a2ensite` is just a symlink helper.** It does not parse the config. If `gci.conf` has a typo, `a2ensite` will happily enable it and the next `reload` will fail. Always `apache2ctl configtest` first.
- **Per-site logs are worth the extra two lines.** Combined logs across many VirtualHosts turn debugging into needle-in-haystack work. Separated logs are trivial to grep.
- **TLS is the next step.** Everything above runs on plaintext HTTP. A production VirtualHost needs a second block listening on `*:443`, with `SSLEngine on`, a certificate from Let's Encrypt or an internal CA, and an HTTP→HTTPS redirect at the top of the port 80 block.

---

## Where This Sits in the Stack

Apache is the application-layer service the rest of this lab series defends. The earlier posts in the series cover the layers in front of it: **pfSense** at the network perimeter, **UFW** at the host filter, **Snort** as the passive sensor watching the traffic that does get through. A misconfigured Apache exposes the host regardless of how well those upstream layers are tuned, so getting `ServerName`, `DocumentRoot`, and TLS right is the application-layer equivalent of "default deny" at the network layer.
