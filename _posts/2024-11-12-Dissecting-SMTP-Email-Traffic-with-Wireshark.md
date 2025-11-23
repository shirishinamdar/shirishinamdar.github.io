---
title: "Dissecting SMTP Email Traffic with Wireshark"
date: 2024-11-12
categories: [Network Analysis, Protocol Study]
tags: [SMTP, Wireshark, Packet Capture, Email Forensics]
description: Step-by-step analysis of SMTP communication captured in Wireshark, revealing timestamps, email client information, message content, and packet structure.
---

## Introduction

This analysis provides a detailed examination of an SMTP packet capture (`SMTP.pcap`), identifying timestamps, client software, email content, and related network parameters.  
**Wireshark** was used to decode and interpret each packet to understand how an email transaction unfolds over the Simple Mail Transfer Protocol (SMTP).

You can follow along by downloading the same capture:  
🔗 [SMTP.pcap — Wireshark Sample Capture](https://wiki.wireshark.org/uploads/__moin_import__/attachments/SampleCaptures/smtp.pcap)

---

## Understanding SMTP

**SMTP (Simple Mail Transfer Protocol)** is an application-layer protocol used for sending and receiving email messages.  
It typically operates on **port 25**, while secure alternatives include **587 (STARTTLS)** and **465 (SMTPS)**.

SMTP exchanges plain text commands and responses — meaning the communication is **not encrypted by default**.  
To protect data, encryption layers like **SSL/TLS** or **STARTTLS** are added to secure the session.

| Port | Protocol | Encryption             |
| ---- | -------- | ---------------------- |
| 25   | SMTP     | None                   |
| 587  | STARTTLS | Optional (TLS upgrade) |
| 465  | SMTPS    | SSL/TLS                |

![SMTP](/assets/img/blog/smtp-wireshark/smtpsa.png)

---

## 1️. When Did It Happen?

The first packet in the capture shows the timestamp:

> **Oct 5, 2009 02:06:11.858334000 EDT**

This marks the start of the email transaction.  
The same timestamp appears across **14 fragments**, which together form the complete email message.

![Timestamp](assets/img/blog/smtp-wireshark/2.png)

This indicates that the email was transmitted as multiple TCP segments but captured as part of a continuous SMTP session.

---

## 2️. The Email Client

By inspecting the **SMTP/IMF** section in Wireshark, the header information identifies the email client used:

> **Microsoft Outlook 12.0**

This provides insight into the mail user agent (MUA) that composed and sent the message.

![Email Client](assets/img/blog/smtp-wireshark/3.png)

---

## 3️. The Email Content

The content of the email can be extracted in two ways:

### Method 1 — Inspect IMF Layer
Open the same frame that identifies the SMTP protocol, then expand **Internet Message Format (IMF)**.  
Here, Wireshark presents each MIME component of the email, including:

![IMF Layer](assets/img/blog/smtp-wireshark/4.png)

- **Plain text** message body (`text/plain`)

- **Attachment**: `NEWS.txt`

![Plain text and Attachment](assets/img/blog/smtp-wireshark/5.png)

Each part of the email is represented as a separate MIME section, allowing granular viewing of both the message and attachments.

### Method 2 — Follow the TCP Stream
Locate the `SMTP: DATA` frame, right-click, and choose **Follow → TCP Stream**.  
This reconstructs the full conversation, including the raw email content as seen by the mail server.  
This approach is especially useful when analyzing message headers or investigating email injection attacks.

![SMTP Stream Data](assets/img/blog/smtp-wireshark/6.png)

![Content](assets/img/blog/smtp-wireshark/7.png)

---

## 4️. Communication Flow and Network Parameters

A good way to understand the overall SMTP conversation is to check the **Protocol Hierarchy Statistics** in Wireshark.

![Protocol Hierarchy Statistics](assets/img/blog/smtp-wireshark/8.png)

From the capture:

- **SMTP** accounts for **46.7%** of packets and **51.5%** of total bytes.  
- All communication occurs over **TCP** (88.3% of packets), confirming SMTP’s connection-oriented design.  
- The **Internet Message Format (IMF)** packets represent **1.7%** of total packets but carry **56.4%** of all bytes — this large size corresponds to the email body and attachments.

Filtering the traffic with Wireshark `smtp || tcp.port == 25` gives access to the full sequence of SMTP commands such as HELO, MAIL FROM, RCPT TO, and DATA.

---

### Network-Level Observations

| Field                | Value                      |
| -------------------- | -------------------------- |
| **Source IP**        | 10.1.10.1.4                |
| **Destination IP**   | 74.53.140.153              |
| **Source Port**      | 1470                       |
| **Destination Port** | 25 (SMTP)                  |
| **Source MAC**       | Cradlepo_3c:17:c2          |
| **Destination MAC**  | Netgear_d9:81:60           |
| **Sender Email**     | gurpartan@patriots.in      |
| **Recipient Email**  | raj_deol2002in@yahoo.co.in |
| **Mail Server**      | 74.53.140.153 (SMTP relay) |

This confirms:

- The SMTP/IMF packet originated from a local host at **10.1.10.1.4**  
- It was sent to an external SMTP server **74.53.140.153**  
- The email was then relayed toward **Yahoo! Mail** servers for final delivery  

---

## Key Takeaways

- SMTP operates over TCP and ensures reliable email delivery.  
- Packet fragmentation is normal for emails with attachments.  
- IMF layers reveal full message bodies, headers, and attachments.  
- **Follow TCP Stream**, **Protocol Hierarchy**, and **IMF decoding** are essential Wireshark features for email forensics.  
- STARTTLS or SMTPS should always be used to avoid plaintext exposure.

---
