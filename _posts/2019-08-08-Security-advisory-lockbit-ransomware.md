---
title: Security Advisory - LockBit Ransomware
author: Shirish Inamdar
date: 2021-08-30 00:00:00 +0800
categories: [Security, Ransomware]
tags: [LockBit, ransomware, security advisory]
---

![LockBit Ransomware](https://digitalrecovery.com/wp-content/uploads/2024/02/Lockbit.webp)

# Background

**Subject:** LockBit Ransomware  
**Type:** Ransomware
**Name/Variant:** ABCD, LockBit

LockBit ransomware is a malicious software designed to block user access to computer systems in exchange for a ransom payment. It will automatically vet for valuable targets, spread the infection, and encrypt all accessible computer systems on a network. This ransomware is used for highly targeted attacks against enterprises Yand other organizations.

## Summary

As a trailblazer in the realm of cybersecurity, I am compelled to shed light on the ever-evolving threat landscape, where adversaries continuously push the boundaries of malicious ingenuity. LockBit, a formidable ransomware strain, stands as a testament to the relentless pursuit of financial gain by malicious actors, preying on enterprises and government organizations worldwide.

| Key Facts         | Details                                                                                   |
| ----------------- | ----------------------------------------------------------------------------------------- |
| Formerly Known As | ABCD Ransomware                                                                           |
| Initial Attacks   | September 2019                                                                            |
| Notable Targets   | Organizations in the US, China, India, Indonesia, Ukraine, and various European countries |
| Modus Operandi    | Ransomware-as-a-Service (RaaS) model, affiliates profit from ransom payments              |
| Target Selection  | Avoids systems in Russia and CIS countries to evade prosecution                           |

Viable targets are organizations that will feel hindered enough by the disruption to pay a substantial ransom and have the financial resources to do so. This can result in sprawling attacks against large enterprises from healthcare to financial institutions. LockBit's automated vetting process intentionally avoids attacking systems local to Russia or any other countries within the Commonwealth of Independent States, presumably to evade prosecution in those areas.

### LockBit 2.0: Raising the Stakes



The new variant of LockBit 2.0 Ransomware is capable of encrypting Windows domains with Active Directory Group Policy policies. Researchers have discovered this novel approach, which automates the interaction and subsequent encryption of Windows domains, adding a formidable layer of complexity to the attack chain.

One notable incident involved the renowned consulting firm Accenture, which confirmed a ransomware attack by LockBit 2.0 on August 11th, 2021. The operators threatened to release the company's data and sell insider information, showcasing the grave consequences organizations face when targeted by this malicious software.

![LockBit Countdown Clock](https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.cybereason.com%2Fblog%2Faccenture-responds-following-lockbit-ransomware-attack&psig=AOvVaw0zwtlA4zNVJcvFaz8daM_q&ust=1713849308445000&source=images&cd=vfe&opi=89978449&ved=0CBIQjRxqFwoTCLiioauI1YUDFQAAAAAdAAAAABAh)

## Technical Analysis

### Attack Flow

Once the malicious file is executed, the following sequence unfolds:

1. The file scans the entire LAN network and attempts to connect to hosts via the SMB port (445) to spread the malicious file across the internal network.
2. An instance of `SVCHOST.exe` is running by the process `DLLhost.exe`, which runs with the following command to bypass the need for User Access Control:
   ...
   C:\WINDOWS\SysWOW64\DllHost.exe /Process id: {3E5FC7F9-9A51-4367-9063-A120244FBEC7}
   ...

This method is known as CMSTP (Client-side Microsoft Service Provider).

![CMSTP](https://www.cynet.com/wp-content/uploads/2022/04/word-image-5-5.png)

3. The ransomware dynamically uses the function `IsWow64Process` to check if the victim's OS is running a x64 system and then uses the functions `Wow64DisableWow64FsRedirection` and `Wow64RevertWow64FsResdirection`. If the malware can access these functions, it will use the first to destroy all shadow volumes and the protections of the OS in the next boot, and later, will recover the redirection with the other function. If it cannot get these functions, LockBit will delete the shadow volume directly through the function `ShellExecuteA` or with the function `CreateProcessA`.

4. The deletion of files within the recycle bin is executed with the function `SHEmptyRecycleBinW`.

5. The `backup.exe` file will execute the payload and encrypt most of the user's files, changing their extensions to `.lockbit`.

6. Immediately after, a ransom note called `Restore-My-Files.txt` will be dropped in several folders on the host.

7. A new instance of `CMD` is launched to execute the following commands:
...
/c wevtutil cl application
/c wevtutil cl security
...
These commands clear logs containing records of login/logout activity or other security-related events specified by the system's audit policy and applications. The attacker hides their tracks to avoid future forensics on the host by the IT/Security Team.

## Preventative Controls

As a cybersecurity professional driven by an unwavering commitment to safeguarding digital frontiers, I cannot emphasize enough the importance of implementing robust preventative measures against threats like LockBit. Here are some essential controls to consider:

- Enforce strong password policies and implement multi-factor authentication across all systems.
- Blacklist the provided Indicators of Compromise (IOCs) for LockBit ransomware.
- Regularly reassess and review user account permissions, removing outdated and unused accounts.
- Ensure system configurations adhere to all security best practices and procedures.
- Maintain regular system-wide backups and clean local machine images for rapid recovery.

## IOCs

The following Indicators of Compromise (IOCs) have been identified for the LockBit ransomware. Monitoring and blocking these IOCs can aid in early detection and prevention efforts.

### Hashes

| Hash                                       |
| ------------------------------------------ |
| `0cc92cccebed351b1b5e6b28082af5e00da28678` |
| `a4c486b0926f55e99d12f749135612602cc4bf64` |
| `307088ae7027b55541311fd70a9337ff3709fccf` |
| ...                                        |

### Domains

- `http://lockbitks2tvnmwk.onion/`
- `lockbitkodidilol.onion`
- `lockbitks2tvnmwk.onion`
- `https://bridges.torproject.org`
- `https://tb-manual.torproject.org/about`
- `https://www.torproject.org/`
- `bridges.torproject.org`
- `tb-manual.torproject.org`
- `www.torproject.org`

## SOC Responsibility

The Security Operations Center (SOC) plays a pivotal role in combating threats like LockBit. As cybersecurity professionals, our responsibilities include:

- Adding the provided IOCs to watchlists and continuously monitoring for potential indicators of compromise.
- Implementing robust security controls and response procedures to mitigate the risk of ransomware infections.
- Conducting regular security assessments and penetration testing to identify potential vulnerabilities proactively.
- Collaborating with incident response teams to develop and refine incident handling procedures specific to ransomware attacks.

## References

- [Cynet Threat Report on LockBit Ransomware](https://www.cynet.com/blog/threat-report-lockbit-ransomware/)
- [AlienVault OTX Pulse on LockBit Ransomware](https://otx.alienvault.com/pulse/5ea6f485a4964cdf88019bd4)
- [SOCRadar: The Story of LockBit Ransomware](https://socradar.io/the-story-of-lockbit-ransomware/)
- [McAfee Blog: Tales from the Trenches - A LockBit Ransomware Story](https://www.mcafee.com/blogs/other-blogs/mcafee-labs/tales-from-the-trenches-a-lockbit-ransomware-story/)

---

In the ever-evolving landscape of cybersecurity, threats like LockBit ransomware serve as a stark reminder of the relentless pursuit of malicious actors and the paramount importance of vigilance and proactive defense. As cybersecurity professionals, it is our solemn duty to stay ahead of the curve, fortifying our defenses and safeguarding the digital frontiers that power our modern world. 