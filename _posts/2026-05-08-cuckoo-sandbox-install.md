---
title: Cuckoo Sandbox Installation for Malware Analysis
date: 2026-05-08 18:54:00 -0400
categories: [Malware Analysis]
tags: [Cuckoo, Sandbox, Malware Analysis, Lab]
description: Installing Cuckoo Sandbox on a Linux host for automated malware analysis: dependencies, configuration, the analyzer VM, and the first detonation of a sample binary.
image:
  path: /assets/img/blog/cuckoo-sandbox-install/image1.png
  alt: Cuckoo Sandbox Installation for Malware Analysis
---

**We will be preparing a complete environment for Cuckoo Sandbox, which
includes installing essential system libraries, databases like MongoDB
and PostgreSQL, and managing Python versions using Anaconda.**

**This setup ensures that Cuckoo can run safely in isolated
environments, execute and monitor suspicious files or URLs, collect
detailed malware behavior data, and store results in a database for
analysis. We are building the full foundation needed to perform
automated, secure malware testing.**

**1. Ubuntu Machine and Install all libraries  
  
Essential dependencies like libffi, libssl, and swig are needed for
Python modules and secure operations in Cuckoo.**  
sudo apt update

sudo apt install libffi-dev libssl-dev libjpeg-dev zlib1g-dev swig

![](/assets/img/blog/cuckoo-sandbox-install/image1.png)  
  
**2. Install MongoDB on Linux Mint 22.1 (Based on Ubuntu 24.04)  
**MongoDB acts as a database backend for storing analysis results.
Installing and enabling it ensures Cuckoo can save and query data.**  
**

![](/assets/img/blog/cuckoo-sandbox-install/image2.png)

**Install required tools**

sudo apt update

sudo apt install curl gnupg -y

**Import MongoDB GPG key**

curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \

sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

**Add MongoDB repository (use jammy repo)**

echo "deb \[ arch=amd64
signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg \] \

https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" |
\

sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list**  
Update and install**

sudo apt update

sudo apt install mongodb-org -y**  
Start MongoDB  
**sudo systemctl start mongod

sudo systemctl enable mongod

sudo systemctl status mongod

**  
3\. Install PostgreSQL  
**Optional for advanced Cuckoo features, especially if you want to use
PostgreSQL instead of SQLite for VM metadata and reporting.**  
**sudo apt install postgresql libpq-dev -y  
**  
**

![](/assets/img/blog/cuckoo-sandbox-install/image3.png)**  
  
**We need Anaconda and Python because Cuckoo Sandbox is built on Python
and requires specific versions and libraries to run correctly. Anaconda
allows us to create isolated Python environments, so Cuckoo can use the
exact Python version it needs (like 2.7) without conflicting with the
system Python or other software. It also simplifies managing
dependencies and packages, ensuring a stable and controlled setup for
malware analysis.**  
4\. Download Anaconda Python 3.7 for Linux 64-bit  
Run the bash script  
**curl -O
[<span class="underline">https://repo.anaconda.com/archive/Anaconda3-2025.12-2-Linux-x86_64.sh</span>](https://repo.anaconda.com/archive/Anaconda3-2025.12-2-Linux-x86_64.sh)  
**  
**

![](/assets/img/blog/cuckoo-sandbox-install/image4.png)**  
  
**

![](/assets/img/blog/cuckoo-sandbox-install/image5.png)

**5. Update conda**

**Updates all packages and dependencies to ensure a stable, secure, and
compatible environment for running Cuckoo Sandbox**

**conda update --all  
**wget
[<span class="underline">https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh</span>](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh)**  
Do you wish to initialize Miniconda3?**

**Yes**

\~/miniconda3/bin/conda init bash

**Then close the terminal completely and open a new one.**

conda -version

**Then type,**

conda update conda

Yes to update packages

**6. Add all version of python to anaconda environment**

conda search python

conda install anaconda-navigator

Anaconda-navigator

Navigator GUI would open

![](/assets/img/blog/cuckoo-sandbox-install/image6.png)

Create python 3.10 environment

![](/assets/img/blog/cuckoo-sandbox-install/image7.png)

Enter into the environment( Cuckoo_Sandbox) by terminal

**7. Install setuptools and cuckoo using pip**

conda create -n cuckoo2 python=2.7

conda activate cuckoo2

pip install -U cuckoo  
  
![](/assets/img/blog/cuckoo-sandbox-install/image8.png)  
Type cuckoo to see if this is installed.

**8. Cuckoo main configuration for general behavior analysis option**

Cuckoo sandbox has configuration file **cuckoo.conf** to know where to
store data, how to run VMs safely, and how to analyze malware properly.

**9. Enable mongodb = yes in
<span class="underline">reporting.conf</span> before run cuckoo
webserver  
**

![](/assets/img/blog/cuckoo-sandbox-install/image9.png)**  
  
Next part will be more of Adding the file in GUI of Cuckoo Sandbox and
malware analysis. UI had few error while opening but will be covered in
next part.  
**
