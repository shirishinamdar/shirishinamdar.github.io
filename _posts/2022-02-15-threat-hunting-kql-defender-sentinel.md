---
title: "Threat Hunting KQL Queries for Microsoft Defender and Azure Sentinel"
date: 2022-02-15 18:00:00 -0500
categories: [Threat Hunting, SIEM]
tags: [KQL, Kusto, Microsoft Defender for Endpoint, ATP, Azure Sentinel, Threat Hunting, Coinminer, Brute Force, USB, PnP, Detection, Project]
description: Seven Kusto Query Language (KQL) queries I use for proactive threat hunting in Microsoft Defender for Endpoint and Azure Sentinel, covering coinminer detection, sustained high CPU, Windows and Linux brute force, rare and uncommon USB or storage devices, and general usage notes for working them into a hunt loop.
---

A working set of **Kusto Query Language (KQL)** queries I use for threat hunting in **Microsoft Defender for Endpoint** and **Azure Sentinel**. The queries cover coinminer detection, sustained high CPU as a behavioral proxy for mining, brute force attempts on Windows and Linux, and a few different angles on rare or unusual USB and storage device activity.

The full repo, with a few extras, is on GitHub: [shirishinamdar/Threat-Hunting-KQL-](https://github.com/shirishinamdar/Threat-Hunting-KQL-).

---

## Query 1, Detect Potential Coinminer Malware

```kql
DeviceProcessEvents
| where ProcessCommandLine has_any ("monero", "xmrig", "cpuminer", "minerd")
    or ProcessCommandLine matches regex @"(?i)(\.exe|\.dll)\s+-o\s+pool"
    or ProcessCommandLine contains "--cpu-priority"
| project Timestamp, DeviceName, AccountName, ProcessCommandLine, InitiatingProcessCommandLine, FileName
| extend Alert = "Potential coinminer activity detected"
```

What it does:

- Searches process command lines for known coinminer terms or patterns.
- Looks for common miner binaries (`monero`, `xmrig`, `cpuminer`, `minerd`).
- Regex matches the `-o pool` argument style typical of mining configurations.
- Catches the `--cpu-priority` flag miners often set.

**Use case:** identify machines running unauthorized mining software, which is usually a sign of compromise or insider misuse.

---

## Query 2, Sustained High CPU as a Mining Indicator

```kql
DevicePerformance
| where Timestamp > ago(1h)
| where CpuUsagePercentage > 90
| summarize AvgCPU = avg(CpuUsagePercentage) by DeviceName
| where AvgCPU > 90
| project DeviceName, AvgCPU
| join kind=inner (
    DeviceProcessEvents
    | where Timestamp > ago(1h)
    | summarize ProcessList = make_set(ProcessCommandLine) by DeviceName
) on DeviceName
| extend Alert = "High CPU usage detected, possible mining activity"
```

What it does:

- Finds devices with consistently high CPU usage (over 90 percent) in the last hour.
- Averages CPU per device and only keeps the ones whose average stays above 90 percent.
- Joins to `DeviceProcessEvents` so the hunt result includes the set of processes that were running on those devices.

**Use case:** catches miners that rename or obfuscate their binaries to dodge name-based detection (Query 1). You're hunting on the behavior, not the string.

---

## Query 3, Brute Force on Windows

```kql
SecurityEvent
| where EventID in (4625, 4771)
| summarize FailedAttempts = count() by TargetAccount, IpAddress, bin(TimeGenerated, 10m)
| where FailedAttempts > 10
| extend Alert = strcat("Potential brute force attack detected. ", FailedAttempts, " failed login attempts in 10 minutes")
```

What it does:

- Filters Windows security events for failed logons (`4625`) and Kerberos pre-auth failures (`4771`).
- Counts failures per `TargetAccount` and `IpAddress` in 10-minute buckets.
- Alerts if more than 10 failures occur in a 10-minute window.

**Use case:** unauthorized access attempts via password guessing on Windows hosts.

---

## Query 4, Brute Force on Linux

```kql
Syslog
| where SyslogMessage contains "Failed password"
| parse SyslogMessage with * "invalid user " User " from " IpAddress " port" *
| summarize FailedAttempts = count() by User, IpAddress, bin(TimeGenerated, 10m)
| where FailedAttempts > 10
| extend Alert = strcat("Potential Linux brute force attack detected. ", FailedAttempts, " failed login attempts in 10 minutes")
```

What it does:

- Filters Syslog for `Failed password` messages.
- Parses the username and source IP out of the message string.
- Same 10-failures-in-10-minutes threshold as the Windows version.

**Use case:** unauthorized access attempts via password guessing on Linux hosts. Pairs naturally with Query 3 for cross-OS coverage.

---

## Query 5, Rare One-Time Devices Connected to a Specific Machine

```kql
let DeviceNameParam = "<replace this with full computer name>";
let devices =
    DeviceEvents
    | where ActionType == "PnpDeviceConnected"
    | extend parsed=parse_json(AdditionalFields)
    | project
        DeviceDescription=tostring(parsed.DeviceDescription),
        ClassName=tostring(parsed.ClassName),
        DeviceId=tostring(parsed.VendorIds),
        VendorIds=tostring(parsed.VendorIds),
        DeviceName, Timestamp ;
devices
| where DeviceName == DeviceNameParam
| summarize TimesConnected=count(), FirstTime=min(Timestamp), LastTime=max(Timestamp) by DeviceId, DeviceDescription, ClassName, VendorIds, DeviceName
| where LastTime - FirstTime < 1d
| join kind=leftanti
  (devices | summarize Machines=dcount(DeviceName) by DeviceId, DeviceDescription, VendorIds | where Machines > 5)
  on DeviceId, DeviceDescription, VendorIds
```

What it does:

- Filters `PnpDeviceConnected` events for one specific machine you set in `DeviceNameParam`.
- Summarizes device connections that appear only briefly (within 24 hours, first to last).
- Then `leftanti` joins out any device that's been seen on more than 5 machines in the org. What's left is the rare, machine-specific stuff.

**Use case:** flag potentially suspicious device connections (unauthorized USBs, exfil devices, malicious hardware) on a sensitive endpoint.

---

## Query 6, Uncommon Storage Devices Across the Org

```kql
DeviceEvents
| where ActionType == "PnpDeviceConnected"
| extend parsed=parse_json(AdditionalFields)
| extend
    DeviceDescription=tostring(parsed.DeviceDescription),
    ClassName=tostring(parsed.ClassName)
| where
    ClassName in ("DiskDrive", "CDROM")
    or ClassName contains "nas"
    or ClassName contains "SCSI"
    or (ClassName == "USB" and DeviceDescription contains "storage")
| summarize ComputerCount=dcount(DeviceName) by ClassName, DeviceDescription, DeviceName
| where ComputerCount < 10
```

What it does:

- Pulls plug-and-play storage connections across the fleet.
- Limits to storage-class devices (DiskDrive, CDROM, NAS, SCSI, USB storage).
- Counts unique computers per device and only keeps devices seen on fewer than 10.

**Use case:** find unauthorized or suspicious storage devices in active use, a common vector for data exfiltration.

---

## Query 7, USB Storage Device Connections

```kql
DeviceEvents
| project Timestamp, DeviceName, ActionType, AdditionalFields
| where ActionType == 'PnpDeviceConnected'
| extend PNP = parsejson(AdditionalFields)
| extend ClassName = PNP.ClassName
| extend DeviceId = PNP.DeviceId
| extend DeviceDescription = PNP.DeviceDescription
| extend VendorId = PNP.VendorIds
| where DeviceId startswith @'USBSTOR\'
| project-away ActionType, AdditionalFields, PNP
| sort by Timestamp desc
```

What it does:

- Pulls every PnP connect event.
- Extracts the class name, device ID, description, and vendor IDs.
- Filters to USB storage by matching `DeviceId` starting with `USBSTOR\`.
- Sorts newest first.

**Use case:** audit USB storage activity for data loss prevention and insider threat detection. Useful as a baseline source for the more refined Queries 5 and 6.

---

## Working These into a Hunt

A few notes on how I actually use the set, not just run them once:

1. **Baseline first.** Run each query in your environment and note what normal looks like. Without a baseline, the alerts they produce are noise.
2. **Hunt the anomalies.** Once you have a baseline, look for changes: new processes, new IPs hitting Query 3 or 4, new USB vendor IDs in Query 7.
3. **Pivot, don't just alert.** When something fires, pull surrounding logs (network connections, parent process tree, file writes) before deciding.
4. **Tune thresholds to your environment.** The 10-failures-in-10-minutes threshold in Queries 3 and 4 is a starting point. Some environments need 5; some need 50.
5. **Feed incident response.** Real hits go to IR. Treat the queries as detection content, not analysis content.
6. **Customize and add.** As you see new techniques in your environment, extend the regex in Query 1, add new event IDs to Query 3, narrow Query 6 to specific high-value subnets, and so on.

These are starting points, not a finished detection program. They pair best with EDR telemetry, threat intelligence, and a defined hunt loop.

The full repo is at [shirishinamdar/Threat-Hunting-KQL-](https://github.com/shirishinamdar/Threat-Hunting-KQL-). Pull requests welcome.
