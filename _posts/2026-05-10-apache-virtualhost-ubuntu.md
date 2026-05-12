---
title: Apache HTTP Server with VirtualHost on Ubuntu
date: 2026-05-10 18:54:00 -0400
categories: [Web, System Administration]
tags: [Apache, VirtualHost, Ubuntu, Web Server, Lab]
description: Installing Apache HTTP Server on Ubuntu, creating a custom site directory, writing a basic HTML page, and configuring a VirtualHost to route a domain to the new site.
image:
  path: /assets/img/blog/apache-virtualhost-ubuntu/cover.svg
  alt: "APACHE — VirtualHost on Ubuntu"
---

# Overview

This week's work focused on three main tasks:

  - Installing and verifying the Apache HTTP Server on an Ubuntu system
    using the apt package manager.

  - Creating a custom website directory and writing a basic HTML page to
    serve via Apache.

  - Configuring a VirtualHost file to route a custom domain to the new
    site, enabling multi-site hosting on a single server.

  - Completing the Flipper Zero ppt presentation.

# Installing Apache on Ubuntu

The first step was to update the package index and install Apache using
Ubuntu's built-in package manager. This ensures all dependencies are
resolved automatically and the latest stable release is installed.

The following two commands were run in sequence:

> sudo apt update
> 
> sudo apt install apache2

After the installation completed, the Apache service started
automatically. To verify the server was running correctly, the server's
IP address( your IP address check via $ifconfig) was entered into a web
browser. The default Apache welcome page loaded successfully, confirming
the web server was operational.

![](/assets/img/blog/apache-virtualhost-ubuntu/image1.png)

*Figure 1 -- Default Apache welcome page confirming successful
installation on Ubuntu.*

The Apache service status can be checked at any time with: **sudo
systemctl status apache2**

![](/assets/img/blog/apache-virtualhost-ubuntu/image2.png)

# Creating the Website Directory & HTML Page

By default, Apache serves content from **/var/www/html**. For this
setup, a new directory was created under **/var/www/** to host a
separate site. This keeps the default Apache site untouched and
demonstrates multi-site capability.

## Creating the Directory

A new folder was created for the site using the following command:

> sudo mkdir /var/www/gci/

## Writing the HTML Page

The terminal was navigated into the new directory and the **nano** text
editor was used to create an **index.html** file:

> cd /var/www/gci/
> 
> sudo nano index.html

The following HTML was written into the file and saved:

> <html>
> 
> <head>
> 
> <title> Northern Virginia Community College </title>
> 
> </head>
> 
> <body>
> 
> <p> I'm running this website on an Ubuntu Server!</p>
> 
> </body>
> 
> </html>

![](/assets/img/blog/apache-virtualhost-ubuntu/image3.png)

*Figure 2 -- index.html file created in /var/www/gci/ using the nano text
editor.*

# Setting Up the VirtualHost Configuration File

Apache stores available site configurations in
**/etc/apache2/sites-available/**. The default configuration file was
used as a base and copied to a new file named **gci.conf** to match the
subdomain being configured.

## Navigating to the Config Directory

> cd /etc/apache2/sites-available/

## Copying the Default Config

> sudo cp 000-default.conf gci.conf

## Editing the Config File

The new file was opened for editing with: **sudo nano gci.conf**

Three directives were added or updated inside the file:

**1. ServerAdmin** -- set to a contact email so users can reach the
administrator if Apache encounters an error:

> ServerAdmin yourname@example.com

**2. DocumentRoot** -- updated to point to the new site directory:

> DocumentRoot /var/www/gci/

**3. ServerName** -- added as a new line (not present in the default
file) to tell Apache which domain maps to this VirtualHost:

> ServerName gci.example.com

The file was saved and nano was exited using Ctrl+O, Enter, then Ctrl+X.

![](/assets/img/blog/apache-virtualhost-ubuntu/image4.png)

*Figure 3 -- gci.conf VirtualHost configuration file with ServerAdmin,
DocumentRoot, and ServerName directives configured.*

# Activating the VirtualHost & Reloading Apache

The **a2ensite** utility was used to activate the new configuration
file:

> sudo a2ensite gci.conf

The terminal confirmed the site was enabled and prompted to reload
Apache. The reload command was run to apply the changes:

> sudo service apache2 reload

The terminal confirmed the site was enabled and prompted to reload
Apache. The reload command was run to apply the changes:

sudo service apache2 reload

Next Step, edit your hosts file. This fakes DNS locally on your own
machine only.

sudo nano /etc/hosts

Add this line at the bottom (replace with your actual server IP):

192.168.x.x gci.example.com

To verify the result, the hostname gci.example.com was entered into a
browser. The custom HTML page loaded correctly, confirming the
VirtualHost was routing traffic to the right directory.

![](/assets/img/blog/apache-virtualhost-ubuntu/image5.png)

*Figure 4 -- Browser showing the custom website hosted at gci.example.com
after VirtualHost activation.*
