---
layout: post
title: "Azure Sentinel Honeypot Setup: Mapping Live Cyber Attacks"
date: 2023-06-01 08:00:00 +0000
categories: [Security, Azure, SIEM]
tags: [Azure Sentinel, Honeypot, Cyber Attacks, Threat Monitoring]
author: "Shirish Inamdar"

---
![Diagram](https://miro.medium.com/v2/resize:fit:828/format:webp/0*jz0J7MsU_MFhrhWJ.gif)

In this tutorial, we will learn how to set up an Azure honeypot virtual machine and configure Azure Sentinel to visualize and analyze live cyber attacks from around the world. By creating an intentionally vulnerable system, we can gain valuable insights into the tactics, techniques, and procedures (TTPs) used by attackers, enabling us to enhance our security posture and incident response capabilities proactively.

# Step 1: Create a Virtual Machine

1. Log in to `portal.azure.com` and create a new virtual machine (VM).
2. This VM will be exposed to the internet, acting as a honeypot for attracting and monitoring cyber attacks from various sources and locations.
3. Keep all resources related to this project in a single resource group for easier management.
4. Choose the "West US" region for the VM's location.
5. Select the "Windows 10" image for the operating system.
6. Use the default VM size.
7. Set a username and password for the VM.
8. Open inbound port 3389 (RDP) for remote access.

 ![VM](https://miro.medium.com/v2/resize:fit:828/format:webp/0*klOdx1Z-qFaz3x8S)

# Step 2: Configure Network Security

1. When configuring the network settings, create a new Network Security Group (NSG) to act as a firewall for the VM.
2. Create a new inbound rule that allows all traffic to the VM.
  - We want to make the VM discoverable by any means necessary, including TCP ping, SYN scans, and ICMP ping, without dropping any traffic.

![Network group](https://miro.medium.com/v2/resize:fit:1400/format:webp/0*7XfAjjdFgUeoq94Z)

# Step 3: Set up Log Analytics Workspace

1. Search for the "Log Analytics Workspace" service in the Azure portal.
2. Create a new Log Analytics Workspace to ingest logs from the virtual machine, including Windows event logs containing geographic information about the attackers.
3. Enable Log Analytics integration with Azure Security Center (now called Microsoft Defender for Cloud) to gather logs from the virtual machine.
![logsAnalytics](https://miro.medium.com/v2/resize:fit:828/format:webp/0*U--bYvePeI2JGYus)

# Step 4: Configure Azure Sentinel

1. Search for "Microsoft Sentinel" in the Azure portal and add it to your Log Analytics Workspace.
2. After connecting Azure Sentinel, copy the IP address of the honeypot VM.
3. Use Remote Desktop Protocol (RDP) to connect to the VM, entering the username and password you set earlier.
4. Disable Windows Defender on the VM to allow unhindered access.
![Firewall] https://miro.medium.com/v2/resize:fit:828/format:webp/0*vVYN5m1qI5mXVPcf

# Step 5: Collect Failed Login Logs

1. Open a Command Prompt on the VM and confirm that it can ping external addresses.
2. Download and run the `Custom_Security_Log_Exporter.ps1` script from the provided GitHub repository (https://github.com/shirishinamdar/HoneynetSOC-Sentinel-Lab/blob/main/Custom_Security_Log_Exporter.ps1).
3. Obtain an API key from `ipgeolocation.io` and add it to the script to retrieve geolocation data for failed login attempts.
4. The script will monitor the event logs for failed login attempts, grab the attacker's IP address, and create a log file with the failed login data.
   

![Failedlogins](https://miro.medium.com/v2/resize:fit:828/format:webp/0*egvyrARViWdLvYJO)

# Step 6: Ingest Custom Logs into Azure Sentinel

1. In the Azure portal, navigate to the Log Analytics Workspace and create a new custom log table.
2. Copy the failed login data from the VM's log file and create a new text file on your local machine.
3. Upload the text file to the custom log table in Azure.
4. Configure the custom log table with the appropriate collection paths and field details.
5. Once the custom log is ingested, you can search for the log name in the Log Analytics workspace to view the failed login logs.

![logs](https://miro.medium.com/v2/resize:fit:828/format:webp/0*vYawkQBXnKqKxJCj)

# Step 7: Visualize and Analyze Cyber Attacks

1. In the Log Analytics workspace, open a failed login log entry and extract fields such as hostname, username, IP address, state, and country.
2. Save the field extractions for latitude and longitude separately.
3. Use Azure Sentinel's built-in mapping capabilities or create custom dashboards and visualizations to display the geographic locations of the cyber attacks in real-time.
4. Analyze the attack patterns, sources, and techniques to enhance your security posture and incident response strategies.

![Geo](https://miro.medium.com/v2/resize:fit:828/format:webp/0*GCfEAtQ4V4ilriMv)

You will have an operational Azure honeypot VM and an integrated Azure Sentinel setup, providing valuable insights into live cyber attacks from around the world. Leverage this knowledge to strengthen your organization's security defenses and stay ahead of emerging threats.