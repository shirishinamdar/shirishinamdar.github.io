---
title: Security Advisory - SysJoker Backdoor
author: Shirish Inamdar
date: 2024-04-03 00:34:00 +0800
categories: [Security, Malware]
tags: [SysJoker, malware, security advisory]
---

![SysJoker Malware](https://research.checkpoint.com/wp-content/uploads/2023/11/banner13432-1024x505.png)

# Background

**Subject:** New SysJoker backdoor  
**Affected Products:** Windows, macOS, and Linux  

A new multi-platform backdoor malware named 'SysJoker' has emerged in the wild, targeting Windows, Linux, and macOS with the ability to evade detection on all three operating systems. The discovery of the new malware comes from researchers at Intezer who first saw signs of its activity in December 2021 after investigating an attack on a Linux-based web server. The first uploads of the malware sample on VirusTotal occurred in the second half of 2021, which also aligns with the C2 domain registration times.

## Summary

SysJoker was first discovered during an active attack on a Linux-based web server of a leading educational institution. After further investigation, researchers found that SysJoker also has Mach-O and Windows PE versions. Based on Command and Control (C2) domain registration and samples found on VirusTotal, the SysJoker attack is estimated to have been initiated during the second half of 2021.

This malware masquerades as a system update and generates its C2 by decoding a string retrieved from a text file hosted on Google Drive. During analysis, the C2 changed three times, indicating the attacker is actively monitoring for infected machines. Based on victimology and malware behavior, SysJoker is assessed to be targeting specific victims. The malware was uploaded to VirusTotal with the `.ts` suffix, typically used for TypeScript files, suggesting a possible attack vector via an infected npm package.

## Technical Details

The SysJoker malware is written in C++, and each sample is tailored for the specific operating system it targets. Both the macOS and Linux samples are fully undetected on VirusTotal.

### Behavioral Analysis

SysJoker's behavior is similar across all three operating systems. Unlike the Mac and Linux samples, the Windows version contains a first-stage dropper, a DLL (`d71e1a6ee83221f1ac7ed870bc272f01`) uploaded to VirusTotal as `style-loader.ts` with only a few detections at the time of writing.

During the analysis, SysJoker exhibited the following behaviors:

- **Dropper Execution:** Executes a first-stage dropper on Windows, while on macOS and Linux, it directly masquerades as a system process.
- **Persistence Mechanism:** Establishes persistence on the infected system by adding entries to the registry run key or creating cron jobs.
- **C2 Communication:** Communicates with its Command and Control (C2) server to receive instructions and upload collected data.
- **Encoding Scheme:** Implements a decoding/encoding scheme using a hardcoded XOR key for communication with the C2.

#### C2 Communication Flow

1. SysJoker decodes a hardcoded Google Drive link hosting a text file named `domain.txt` containing an encoded C2 address.
2. The malware decodes the C2 address and sends the collected user's information to the C2's `/api/attach` directory as an initial handshake.
3. The C2 responds with a unique token, which is used as an identifier for subsequent communications.
4. SysJoker runs a loop, sending requests to the C2's `/api/req` directory with the unique token to receive instructions.
5. The C2 can respond with instructions such as `exe` (drop and run an executable), `cmd` (run a command and upload the response), `remove_reg` (self-deletion), and `exit`.

![SysJoker C2 Communication](/assets/images/sysjoker-c2.jpg)

### IoCs Tailored for Target Systems

To aid in detection and prevention efforts, the following Indicators of Compromise (IoCs) are provided, categorized by the target operating system.

#### For ELF (Linux)

- `8a7f6c4d6e81f6e5e7c8734ed8f4a9a62124aca9d7992545c3db8b2e5a438c1a`
- `b80165a108b9d1aa1d85ef40197a64d4b3537573b3dc091acda01eb1f1eb29c2`
- `0e65b4244f7ded4c2792bc99e268b045eba2b6a1b8e05f3d6e17515d4293c47e`

#### For MAC (macOS)

- `99ff67021a8359e11d35d7dfc0e902566dea98c17ad18be56ab28873445d4559`
- `3f9565c6616d89bf5d91fea1b041f0b62c9dff0f8b0a71af625f2a46b7ddd016`
- `8eff89cb2360af54ff86622c975504cdcc5a83cb150ccfeb2addd6634e02cccd`

#### For Windows

- `9d9c3aa5f54828332bbcd11db379f96641f0c1f84d73b7afc51b3508f74f86c7`
- `d33f0a39113fc54975b497f4f429706bceb864751058ed3bbe8e9ba63970c754`
- `e556cf63f5e805cc161a95b5ec0346bce013030ceccbc21deba5c86ec6b7d273`

#### URLs

- `https://cdnfiles[.]priv8[.]com/SysJoker/config.txt`
- `https://updatenow[.]tech/macupdate/SysJoker.php`
- `https://quickupdatenow[.]com/winupdate/SysJoker.php`

## Detection and Preventative Controls

To detect and prevent SysJoker infections, we recommend the following steps:

1. **Memory Scanning:** Use memory scanners to detect the SysJoker payload in memory.
2. **EDR Monitoring:** Employ endpoint detection and response (EDR) tools to monitor for suspicious behaviors.
3. **Network Traffic Analysis:** Implement network traffic analysis to identify C2 communications.
4. **Patch Management:** Keep software and systems updated to patch known vulnerabilities exploited by SysJoker.
5. **User Awareness:** Educate users about phishing and social engineering tactics used to distribute malware.

If you have been compromised by SysJoker, follow these steps:

1. Kill all processes related to the malware and manually delete the files and the relevant persistence mechanism.
2. Run a memory scanner to ensure that all malicious files have been removed from the infected system.
3. Investigate potential entry points, check firewall configurations, and update all software tools to the latest available versions.
4. Block all the listed IoCs.

## SOC Responsibility

The Security Operations Center (SOC) will monitor device traffic against the provided IoCs and take appropriate actions to detect and mitigate potential SysJoker infections.

## References

- [Intezer Report on SysJoker](https://www.intezer.com/blog/malware-analysis/new-backdoor-sysjoker/)
- [BleepingComputer Article on SysJoker](https://www.bleepingcomputer.com/news/security/new-sysjoker-backdoor-targets-windows-macos-and-linux/)

---

This comprehensive security advisory provides detailed information about the SysJoker malware, its behavior, detection methods, and preventative controls. Stay vigilant and take the necessary steps to protect your systems from this emerging threat.