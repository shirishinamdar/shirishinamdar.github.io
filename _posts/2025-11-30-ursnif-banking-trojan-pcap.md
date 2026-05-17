---
title: "Investigating an Ursnif (Zeus Panda Banker) Infection from a PCAP"
date: 2025-11-30 18:00:00 -0500
categories: [Malware Analysis, Threat Intelligence]
tags: [Ursnif, Banking Trojan, PCAP, Wireshark, NetworkMiner, VirusTotal, MITRE ATT&CK, Project]
description: A full malware-traffic-analysis exercise on a Thanksgiving-scenario PCAP — triaging the IDS alerts, correlating through VirusTotal and Dynamite Project, extracting the host details and executable with NetworkMiner, and pulling the malicious URL out of Wireshark.
image:
  path: /assets/img/blog/ursnif-malware-traffic-analysis/image4.png
  alt: "NetworkMiner detecting and quarantining the Ursnif sample from the PCAP."
---

This is a full malware-traffic-analysis exercise on a captured PCAP — answering seven specific questions about an infected Windows host.

**The questions to answer:**

- What was the date and time the malicious traffic started?
- What is the MAC address of the infected Windows host?
- What is the host name of the infected Windows host?
- What is the user account name used on the infected Windows host?
- What URL in the PCAP returned a Windows executable file?
- What is the size of the Windows executable file from that URL?
- What type of malware is the Windows executable returned from that URL?

---

## 1. Hypothesis

![alerts.txt — IDS alerts establishing the initial hypothesis.](/assets/img/blog/ursnif-malware-traffic-analysis/image9.png)

From `alerts.txt` we see:

- MalDoc Requesting Ursnif Payload
- ET POLICY PE EXE or DLL Windows file download
- Ursnif Variant CnC Beacon
- Zeus Panda Banker / Ursnif Malicious SSL Certificate

An infected internal host (`10.22.15.119`) downloaded a malicious Windows executable from `46.29.160.132`, which may be associated with **Ursnif / Zeus Panda Banker malware**, and is now performing C2 communications over SSL.

---

## 2. MITRE ATT&CK

[Ursnif](https://attack.mitre.org/software/S0386) is a **banking trojan** and variant of the Gozi malware, observed being spread through various automated exploit kits, [Spearphishing Attachments](https://attack.mitre.org/techniques/T1566/001), and malicious links. Ursnif is associated primarily with data theft, but variants also include components (backdoors, spyware, file injectors, etc.) capable of a wide variety of behaviors.

**Initial vector:** Malicious document → PE/EXE download. **T1059.001** and **T1059.005** — Ursnif droppers have used PowerShell in download cradles to download and execute the malware's full executable payload, and have used VBA macros to do the same.

![Ursnif MITRE ATT&CK reference.](/assets/img/blog/ursnif-malware-traffic-analysis/image16.png)

**C2 Communication:** The infected host (`10.22.15.119`) engaged in HTTP/HTTPS communications with multiple Ursnif C2 servers (`192.162.244.171` and `46.29.160.132`) — **T1071.001** Ursnif has used HTTPS for C2. Alerts indicate that data exfiltration over these C2 channels likely occurred — **T1041** Ursnif has used HTTP POSTs to exfil gathered information, with SSL and malicious certificate detections supporting this.

---

## 3. Threat Intelligence

Sources used: **VirusTotal**, **Dynamite Project**.

### VirusTotal

VirusTotal categorizes this as malware, trojan, and shellcode — with community score zero (indicator of being clean / benign behaviour).

![VirusTotal categorization for the captured traffic.](/assets/img/blog/ursnif-malware-traffic-analysis/image6.png)

From the details tab we get information about start and end time of the activity.

![VirusTotal details — start and end time of the activity.](/assets/img/blog/ursnif-malware-traffic-analysis/image7.png)

> **Q1 — What was the date and time the malicious traffic started?**
> **Solution: `2018-11-7 21:40:47`**

### Dynamite Project

From this tool we look at the artifacts section and correlate our information from `alerts.txt`, where the executable file was downloaded from possible infected host `10.22.15.119` via the C2 channel `46.29.160.132`.

We saw a file named **`FkGguv3jLGmxojSWbc.file`** which is categorized under File Type `x-dosexec`. It is not exactly `traffic.pcap`, so we have to know the specific executable file name for that.

![Dynamite Project artifacts — candidate executable surfaced.](/assets/img/blog/ursnif-malware-traffic-analysis/image14.png)

We suspect this is the executable file that was downloaded, and when we add that hash of the file in VirusTotal it relates to **Banking Trojan Ursnif** and being highly malicious.

![VirusTotal hash lookup — Ursnif banking trojan.](/assets/img/blog/ursnif-malware-traffic-analysis/image5.png)

C2 channel target IP belongs to **LLC Baxet, Russia** and also was found to be malicious.

![IP reputation lookup on the C2 endpoint 46.29.160.132 (LLC Baxet, Russia).](/assets/img/blog/ursnif-malware-traffic-analysis/image8.png)

We get more information from the details of the file — Windows Executable file.

![Detailed file metadata — Windows Executable.](/assets/img/blog/ursnif-malware-traffic-analysis/image11.png)

---

## 4. Evidence Sources

- **PCAP file (`traffic.pcap`)** — primary evidence.
- **HTTP logs** — EXE download.
- **DNS logs** — Domain lookups for C2.
- **`alerts.txt`** — containing IDS/IPS alerts that document potentially malicious network activity, including timestamps, source and destination IPs, protocols, and threat signatures.

---

## 5. Tools

- **Wireshark** — to inspect HTTP/SSL traffic in the PCAP.
- **NetworkMiner** — to extract the EXE and more detailed information about the infected host such as MAC address, hostname, etc.

---

## NetworkMiner

As soon as we added the PCAP into NetworkMiner there was a detection from MS Defender stating an alert was found — Ursnif — which were quarantined and removed.

![Microsoft Defender quarantining the Ursnif sample on PCAP load.](/assets/img/blog/ursnif-malware-traffic-analysis/image4.png)

As we got to know from `alerts.txt`, `10.22.15.119` is an infected host.

> **Q2 — What is the MAC address of the infected Windows host?**
> **Sol: `00112FD16E52`**

> **Q3 — What is the host name of the infected Windows host?**
> **Sol: `DANGER-WIN-PC`**

> **Q4 — What is the user account name used on the infected Windows host?**
> **Sol: `Carlos Danger`** — we get this information from the **Credentials** tab in NetworkMiner.

![NetworkMiner Credentials tab — user account "Carlos Danger".](/assets/img/blog/ursnif-malware-traffic-analysis/image13.png)

![NetworkMiner host details for the infected workstation.](/assets/img/blog/ursnif-malware-traffic-analysis/image10.png)

From the **Files** tab we also found the executable file from the infected file to the C2 channel we found earlier. We will extract this and take out the hash of that file.

![NetworkMiner Files tab — extracting the executable.](/assets/img/blog/ursnif-malware-traffic-analysis/image12.png)

We see that it is similar results to what we got earlier from Dynamite Project.

![VirusTotal result for the extracted executable.](/assets/img/blog/ursnif-malware-traffic-analysis/image2.png)

> **Q6 — What is the size of the Windows executable file from that URL?**
> **A: `439808 B`**

> **Q7 — What type of malware is the Windows executable returned from that URL?**
> **A: Trojan**

---

## Wireshark

Now we know the exact name for the executable file and the communication as well from the infected source to the C2 channel. We can get the URL from which the executable file was returned.

> **Q5 — What URL in the PCAP returned a Windows executable file?**
> **A: `http://shumbildac.com/WES/fatog.php?l=ngul5.xap`**

This is shown by the GET request to that path, followed by an HTTP 200 OK response delivering an `application/octet-stream` beginning with the MZ header of a Windows executable.

![Wireshark — GET request returning the Windows executable.](/assets/img/blog/ursnif-malware-traffic-analysis/image15.png)

We also see that the URL requested from the client is also malicious.

![Reputation check — shumbildac.com flagged as malicious.](/assets/img/blog/ursnif-malware-traffic-analysis/image1.png)
