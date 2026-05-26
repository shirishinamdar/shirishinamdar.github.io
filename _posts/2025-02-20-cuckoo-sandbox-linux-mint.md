---
title: "Cuckoo Sandbox Installation on Linux Mint"
date: 2025-02-20 18:00:00 -0500
categories: [Malware Analysis, Sandbox]
tags: [Cuckoo Sandbox, MongoDB, PostgreSQL, Anaconda, Miniconda, Python, Malware Analysis, Linux Mint, Ubuntu, Project]
description: Standing up a complete Cuckoo Sandbox environment on Linux Mint 22.1, system libraries, MongoDB 7.0, PostgreSQL, an Anaconda based Python 2.7 environment, the Cuckoo install via pip, and enabling MongoDB reporting before launching the web interface.
image:
  path: /assets/img/blog/cuckoo-sandbox-linux-mint/image6.png
  alt: "Anaconda Navigator running on Linux Mint with the Cuckoo Sandbox environment listed."
---

This walkthrough builds a complete Cuckoo Sandbox environment on **Linux Mint 22.1** (based on Ubuntu 24.04). The setup installs the system libraries, MongoDB and PostgreSQL, an Anaconda based Python environment, and Cuckoo itself, then enables MongoDB reporting before the web interface is launched.

Cuckoo runs suspicious files and URLs inside isolated VMs, monitors their behavior, and writes the results to a database for analysis. The pieces below are the foundation for that workflow.

---

## Step 1, Install System Libraries

Essential dependencies like `libffi`, `libssl`, and `swig` are needed for Python modules and secure operations in Cuckoo.

```bash
sudo apt update
sudo apt install libffi-dev libssl-dev libjpeg-dev zlib1g-dev swig
```

![apt installing libffi, libssl, libjpeg, zlib1g and swig on Linux Mint.](/assets/img/blog/cuckoo-sandbox-linux-mint/image1.png)

---

## Step 2, Install MongoDB 7.0

MongoDB acts as the database backend for storing analysis results. Installing and enabling it lets Cuckoo save and query data.

![MongoDB about to be installed for Cuckoo's reporting backend.](/assets/img/blog/cuckoo-sandbox-linux-mint/image2.png)

```bash
# Install required tools
sudo apt update
sudo apt install curl gnupg -y

# Import MongoDB GPG key
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add MongoDB repository (jammy repo works on Ubuntu 24.04 base)
echo "deb [ arch=amd64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] \
https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update and install
sudo apt update
sudo apt install mongodb-org -y

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
sudo systemctl status mongod
```

---

## Step 3, Install PostgreSQL

PostgreSQL is optional but worth installing for advanced Cuckoo features, especially if you want PostgreSQL instead of SQLite for VM metadata and reporting.

```bash
sudo apt install postgresql libpq-dev -y
```

![PostgreSQL installed alongside MongoDB.](/assets/img/blog/cuckoo-sandbox-linux-mint/image3.png)

---

## Why Anaconda and Python

Cuckoo Sandbox is built on Python and requires specific versions and libraries to run correctly. Anaconda lets us create isolated Python environments, so Cuckoo can use the exact Python version it needs (Python 2.7) without conflicting with the system Python or other software. It also simplifies managing dependencies and packages, which is important for a stable malware analysis setup.

---

## Step 4, Download Anaconda

```bash
curl -O https://repo.anaconda.com/archive/Anaconda3-2025.12-2-Linux-x86_64.sh
```

![Downloading the Anaconda3 installer script.](/assets/img/blog/cuckoo-sandbox-linux-mint/image4.png)

![Anaconda3 installation prompts during the bash run.](/assets/img/blog/cuckoo-sandbox-linux-mint/image5.png)

---

## Step 5, Update conda

Updating all packages and dependencies keeps the environment stable, secure, and compatible for Cuckoo.

```bash
conda update --all
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
# Answer "Yes" when asked: Do you wish to initialize Miniconda3?

~/miniconda3/bin/conda init bash
# Close the terminal completely and open a new one

conda --version
conda update conda
# Answer "Yes" to update packages
```

---

## Step 6, Add Python to the Anaconda Environment

```bash
conda search python
conda install anaconda-navigator
anaconda-navigator
```

The Navigator GUI opens, where I created a Python 3.10 environment first.

![Anaconda Navigator after launch on Linux Mint.](/assets/img/blog/cuckoo-sandbox-linux-mint/image6.png)

![Creating the Python 3.10 environment in Anaconda Navigator.](/assets/img/blog/cuckoo-sandbox-linux-mint/image7.png)

Then I dropped into the environment from a terminal to install Cuckoo itself.

---

## Step 7, Install Cuckoo

```bash
conda create -n cuckoo2 python=2.7
conda activate cuckoo2
pip install -U cuckoo
```

![pip install -U cuckoo completing inside the cuckoo2 conda env.](/assets/img/blog/cuckoo-sandbox-linux-mint/image8.png)

```bash
cuckoo
```

Running `cuckoo` confirms the install.

---

## Step 8, Cuckoo Main Configuration

Cuckoo's main configuration file `cuckoo.conf` tells the sandbox where to store data, how to run VMs safely, and how to analyze malware properly.

---

## Step 9, Enable MongoDB Reporting

Before launching the Cuckoo web interface, set `enabled = yes` for the MongoDB section in `reporting.conf`. Without this, results won't be written to MongoDB and the web UI won't have data to display.

![reporting.conf with MongoDB enabled = yes.](/assets/img/blog/cuckoo-sandbox-linux-mint/image9.png)

---

The next part covers loading a sample through the Cuckoo web UI and walking through the analysis output. The UI had a few errors on first open which I'll cover separately.
