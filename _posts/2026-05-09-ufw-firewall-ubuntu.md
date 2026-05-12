---
title: UFW Host-Based Firewall on Ubuntu
date: 2026-05-09 18:54:00 -0400
categories: [Network Security, Firewalls]
tags: [UFW, Firewall, Ubuntu, iptables, Lab]
description: Configuring UFW (Uncomplicated Firewall) on Ubuntu as a host-based filter — default-deny policies, allow rules per service, status verification, and the iptables relationship.
image:
  path: /assets/img/blog/ufw-firewall-ubuntu/cover.svg
  alt: "UFW — Host-Based Firewall on Ubuntu"
---

# Overview  
  
Completed the documentation of UFW lab. With approval from you, this can be used as project for ITN 263.  
  
Uncomplicated Firewall (UFW)

Uncomplicated Firewall (**UFW**) is a frontend interface for
**iptables** designed to simplify host-based firewall management on
Linux systems. While you have already worked with iptables rules
directly and configured pfSense at the network perimeter, this lab
focuses on **endpoint-level firewall control** the last line of defense
on an individual host.

In this lab you will install and configure UFW on your Kali Linux VM,
apply a structured rule set, test and verify your firewall behavior, and
critically analyze how UFW commands map to the underlying iptables
chains you already know.

## Learning Objectives

  - Install and verify UFW on a Kali Linux host( Cyberrange: Cyber
    Basics)

  - Configure default deny/allow policies

  - Write UFW rules for services, ports, and specific IP addresses

  - Enable and interpret UFW logging

  - **Connect UFW syntax to iptables** rules using **ufw show added**
    and **iptables -L**

  - Apply firewall rules to a simulated threat scenario

<table>
<tbody>
<tr class="odd">
<td><p><strong>⚠ Before You Begin</strong></p>
<p>UFW is not installed or enabled by default on Kali Linux.</p>
<p>All commands in this lab require root privileges. Use: sudo su OR prefix each command with sudo.</p>
<p>Take a screenshot after each task that requests one. Paste screenshots directly into this document.</p>
<p>Do NOT run: ufw --force reset unless specifically instructed. (It removes all your rules.)</p></td>
</tr>
</tbody>
</table>

<table>
<tbody>
<tr class="odd">
<td><p><strong>ℹ Single-VM Design</strong></p>
<p>This lab runs entirely inside your Kali VM. No second machine is required.</p>
<p>You will simulate network services using netcat (nc) and loopback (127.0.0.1) traffic to test rules.</p></td>
</tr>
</tbody>
</table>

# Part 1 -- UFW Installation and Status \[10 pts\]

In this section you will install UFW, confirm it is present, and
document the default state before making any changes.

## Task 1.1 -- Install UFW

1.  Open a terminal in your Kali VM and gain root access:

|         |
| ------- |
| sudo su |

2.  Update your package list and install UFW:

<table>
<tbody>
<tr class="odd">
<td><p>apt update</p>
<p>apt install ufw -y</p></td>
</tr>
</tbody>
</table>

3.  Verify the installation:

|             |
| ----------- |
| ufw version |

|                                                                                      |
| ------------------------------------------------------------------------------------ |
| **Q1.1 -- What version of UFW was installed? Paste the output of ufw version below.** |
| 

![](/assets/img/blog/ufw-firewall-ubuntu/image1.png)              |

## Task 1.2 -- Check Default Status

4.  Check UFW's current status before enabling it:

|                    |
| ------------------ |
| ufw status verbose |

<table>
<tbody>
<tr class="odd">
<td><p><strong>ℹ Expected output</strong></p>
<p>Status: inactive</p>
<p>UFW ships disabled. You have not enabled it yet -- that is correct at this stage.</p></td>
</tr>
</tbody>
</table>

|                                                                                                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Q1.2 -- Is UFW currently active or inactive? Why is checking status BEFORE enabling it a good practice?**                                                         |
| Inactive. Enabling a firewall without reviewing rules can block services (web, SSH, APIs), breaking your system. Yes it its necessary to check before enabling it. |

**Screenshot required:** Take a screenshot showing the output of **ufw
status verbose** before enabling.

![](/assets/img/blog/ufw-firewall-ubuntu/image2.png)

# Part 2 -- Default Policy Configuration \[15 pts\]

Default policies define the **baseline behavior** of your firewall --
what happens to traffic that does not match any explicit rule. This is
the most important decision you make when configuring a host firewall.

## Task 2.1 -- Set Default Deny Policies

5.  Set the default policy to deny all incoming traffic:

|                           |
| ------------------------- |
| ufw default deny incoming |

6.  Set the default policy to allow all outgoing traffic:

|                            |
| -------------------------- |
| ufw default allow outgoing |

7.  Confirm both policies are set:

|                    |
| ------------------ |
| ufw status verbose |

<table>
<tbody>
<tr class="odd">
<td><p><strong>⚠ Why default deny incoming?</strong></p>
<p>A default ALLOW policy means any service you accidentally start is immediately reachable.</p>
<p>A default DENY policy means nothing is reachable unless you explicitly permit it.</p>
<p>This is the principle of least privilege applied at the network layer.</p></td>
</tr>
</tbody>
</table>

## Task 2.2 -- Enable UFW

8.  Enable UFW with the current policy set:

|            |
| ---------- |
| ufw enable |

<table>
<tbody>
<tr class="odd">
<td><p><strong>⚠ Warning</strong></p>
<p>If you are connected to this machine via SSH, enabling UFW without an SSH allow rule will lock you out.</p>
<p>In this lab you are working directly on the VM console, so this is safe to proceed.</p></td>
</tr>
</tbody>
</table>

9.  Confirm UFW is now active:

|                    |
| ------------------ |
| ufw status verbose |

**Screenshot required:** Take a screenshot showing UFW enabled with
default policies set.

![](/assets/img/blog/ufw-firewall-ubuntu/image3.png)

|                                                                                                                                                                            |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q2.2 -- What does UFW do with a packet that matches NO rules when default incoming is DENY? Where in the iptables chain does this decision happen? (Hint: ufw show raw)** |
| It's dropped by the default policy, and this happens at the end of the INPUT chain after all UFW rules are checked.                                                        |

# Part 3 -- Service and Port Rules \[25 pts\]

With a baseline deny policy in place, you will now build a rule set that
permits only specific, necessary traffic. This mirrors real-world
hardening of a Linux server.

## Task 3.1 -- Allow SSH (Port 22)

10. Allow incoming SSH connections:

|               |
| ------------- |
| ufw allow ssh |

11. Verify the rule was added:

|                     |
| ------------------- |
| ufw status numbered |

<table>
<tbody>
<tr class="odd">
<td><p><strong>ℹ UFW service name vs. port number</strong></p>
<p>UFW can use service names (ssh, http, https) or port numbers (22, 80, 443).</p>
<p>'ufw allow ssh' and 'ufw allow 22/tcp' are functionally identical.</p>
<p>Service name rules rely on /etc/services for resolution.</p></td>
</tr>
</tbody>
</table>

|                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------ |
| **Q3.1 -- Run: ufw show added What is the exact iptables-style rule that UFW created for the SSH allow? Write it below.** |
| ufw allow 22/tcp                                                                                                         |

## Task 3.2 -- Allow HTTP and HTTPS

12. Allow incoming web traffic on ports 80 and 443:

<table>
<tbody>
<tr class="odd">
<td><p>ufw allow 80/tcp</p>
<p>ufw allow 443/tcp</p></td>
</tr>
</tbody>
</table>

13. Verify the current rule set:

|                     |
| ------------------- |
| ufw status numbered |

**Screenshot required:** Take a screenshot showing all rules added so
far (ssh, 80/tcp, 443/tcp).

![](/assets/img/blog/ufw-firewall-ubuntu/image4.png)

|                                                                                                                                                                                                      |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q3.2 -- A student argues: 'We should just allow 80/tcp and 443/tcp together with one rule.' Is that possible in UFW? Write the command. Is it better practice to split them or combine them? Why?** |
| Split them into separate rules, because it gives clear visibility and finer control (logging, disabling one without affecting the other).                                                            |

## Task 3.3 -- Allow a Custom Port Range

A custom application uses ports 8000-8080 TCP. Allow that range:

14. Add the port range rule:

|                         |
| ----------------------- |
| ufw allow 8000:8080/tcp |

15. Verify it appears in the rule list:

|                     |
| ------------------- |
| ufw status numbered |

<table>
<tbody>
<tr class="odd">
<td><strong>Q3.3 -- What is a realistic security concern with allowing a broad port range like 8000-8080? In a production environment, what would you do instead?</strong></td>
</tr>
<tr class="even">
<td><p>It may expose unintended services running in that range (attack surface increases).</p>
<p>Only allow specific required ports (e.g., 8000 or 8080 individually) or restrict access by IP address / application rule instead of a whole range.</p></td>
</tr>
</tbody>
</table>

## Task 3.4 -- Deny a Specific Port Explicitly

Port 23 (Telnet) should never be allowed -- even if it would otherwise be
permitted by another rule. Add an explicit deny:

16. Deny Telnet:

|                 |
| --------------- |
| ufw deny 23/tcp |

17. Check the rule list:

|                     |
| ------------------- |
| ufw status numbered |

|                                                                                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q3.4 -- UFW processes rules in order. If you later add 'ufw allow 23/tcp', which rule takes effect? How does UFW handle rule conflicts? (Hint: rules are processed top-down like iptables chains.)** |
| The most specific matching rule that appears first in the chain takes effect, and UFW resolves conflicts by top-down processing (first match wins), not by "latest rule wins."."                      |

# Part 4 -- IP-Based Rules and Logging \[20 pts\]

Port-based rules are necessary but not sufficient. Real-world firewalls
also filter by source IP. In this section you will add IP-based rules
and enable logging so that firewall activity is auditable.

## Task 4.1 -- Allow a Trusted IP Address

Allow all traffic from the loopback address and a simulated trusted
management IP (192.168.100.10):

18. Allow loopback (localhost) communication:

|                          |
| ------------------------ |
| ufw allow from 127.0.0.1 |

19. Allow all traffic from a trusted host:

|                               |
| ----------------------------- |
| ufw allow from 192.168.100.10 |

20. Allow traffic from an entire trusted subnet:

|                              |
| ---------------------------- |
| ufw allow from 10.10.10.0/24 |

21. Verify all current rules:

|                     |
| ------------------- |
| ufw status numbered |

**Screenshot required:** Screenshot of the full numbered rule list at
this point.
![](/assets/img/blog/ufw-firewall-ubuntu/image5.png)

<table>
<tbody>
<tr class="odd">
<td><strong>Q4.1 -- What is the difference between 'ufw allow from 192.168.100.10' and 'ufw allow from 192.168.100.10 to any port 22'? Which is more secure, and why?</strong></td>
</tr>
<tr class="even">
<td><p>ufw allow from 192.168.100.10 allows all traffic from that IP.</p>
<p>ufw allow from 192.168.100.10 to any port 22 allows only SSH (port 22) from that IP.</p>
<p>The second one is more secure, because it follows least privilege.</p></td>
</tr>
</tbody>
</table>

## Task 4.2 -- Block a Specific Source IP

Simulate blocking a known malicious source IP:

22. Add a deny rule for a specific source:

|                            |
| -------------------------- |
| ufw deny from 203.0.113.99 |

<table>
<tbody>
<tr class="odd">
<td><p><strong>ℹ RFC 5737 Documentation Addresses</strong></p>
<p>203.0.113.0/24 is reserved for documentation and examples (RFC 5737).</p>
<p>It will never route on a real network, making it safe to use in lab exercises.</p></td>
</tr>
</tbody>
</table>

23. Verify the rule:

|                     |
| ------------------- |
| ufw status numbered |

|                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q4.2 -- In a real incident response scenario, you discover port scans originating from 203.0.113.99. Is blocking a single IP sufficient? What additional steps should a SOC analyst take? (Think: persistence, lateral movement, other hosts.)**                                                                                                                       |
| No, blocking a single IP is not sufficient because attackers can use other IPs or compromised systems. You should analyze logs to see if other hosts were targeted or compromised. Also check for lateral movement and any signs of persistence like new users or scheduled tasks. Finally, update detection rules and monitor for similar activity across the network. |

## Task 4.3 -- Enable UFW Logging

24. Enable UFW logging at the low level:

|                |
| -------------- |
| ufw logging on |

25. Check that logging is active:

|                    |
| ------------------ |
| ufw status verbose |

26. View the firewall log:

<table>
<tbody>
<tr class="odd">
<td><p>tail -n 20 /var/log/ufw.log</p>
<p># If empty, generate some blocked traffic:</p>
<p>nc -zv 127.0.0.1 9999 2&gt;&amp;1 # attempt a connection to a blocked port</p></td>
</tr>
</tbody>
</table>

**Screenshot required:** Screenshot showing ufw logging on in the status
output OR ufw.log entries.
![](/assets/img/blog/ufw-firewall-ubuntu/image6.png)

|                                                                                                                                                                                                                                                                   |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Q4.3 -- What information does each UFW log entry contain? List at least four fields and explain what each tells a security analyst.**                                                                                                                            |
| A UFW log entry usually includes timestamp (when the event occurred), source IP (who sent the traffic), destination IP/port (what was targeted), protocol (TCP/UDP used), and action (ALLOW/DROP/REJECT) which tells whether the firewall permitted or blocked it |

# Part 5 -- Rule Analysis and iptables Comparison \[20 pts\]

UFW is a **wrapper** around iptables. Everything UFW does is translated
into iptables rules under the hood. This section bridges UFW back to
your existing iptables knowledge and requires you to think critically
about what the rules actually mean.

## Task 5.1 -- View Underlying iptables Rules

27. Show the raw iptables rules that UFW has generated:

<table>
<tbody>
<tr class="odd">
<td><p>ufw show raw</p>
<p># OR view iptables directly:</p>
<p>iptables -L -n -v --line-numbers</p></td>
</tr>
</tbody>
</table>

**Screenshot required:** Screenshot of iptables -L output.

|                                                                         |
| ----------------------------------------------------------------------- |
| 

![](/assets/img/blog/ufw-firewall-ubuntu/image7.png) |

## Task 5.2 -- Delete and Re-Add a Rule

28. List rules with numbers:

|                     |
| ------------------- |
| ufw status numbered |

29. Delete the Telnet deny rule by its number (find the rule number
    first):

|                             |
| --------------------------- |
| ufw delete \[RULE_NUMBER\] |

30. Confirm it is gone, then re-add it:

<table>
<tbody>
<tr class="odd">
<td><p>ufw status numbered</p>
<p>ufw deny 23/tcp</p></td>
</tr>
</tbody>
</table>

Screenshot showing 23/tcp port added

![](/assets/img/blog/ufw-firewall-ubuntu/image8.png)

## Task 5.3 -- Comparison Questions

Answer the following questions based on your lab experience and prior
iptables knowledge.

|                                                                                                        |
| ------------------------------------------------------------------------------------------------------ |
| **Q5.3 -- Write the equivalent raw iptables command for: ufw allow from 10.10.10.0/24 to any port 443** |
| iptables -A INPUT -s 10.10.10.0/24 -p tcp --dport 443 -j ACCEPT                                        |

# Part 6 -- Threat Scenario Challenge \[10 pts\]

<table>
<tbody>
<tr class="odd">
<td><p><strong>SCENARIO</strong></p>
<p>You are the security administrator for a Kali Linux development server. The following security requirements have been handed to you:</p>
<ol type="a">
<li><p>Only your internal IT team (subnet 172.16.5.0/24) should be able to SSH into this machine.</p></li>
<li><p>The server runs a public-facing web application on port 8443 (HTTPS).</p></li>
<li><p>All other inbound traffic must be denied.</p></li>
<li><p>A threat intelligence feed has identified 198.51.100.0/24 as a known malicious range -- block it explicitly.</p></li>
<li><p>Logging must be enabled so that denied traffic is auditable.</p></li>
</ol></td>
</tr>
</tbody>
</table>

## Task 6.1 -- Implement the Rule Set

Using only UFW commands, implement all five requirements above. You may
first run:

|                   |
| ----------------- |
| ufw --force reset |

to start from a clean state, then rebuild the firewall from scratch.

**Screenshot required:** Screenshot of your final **ufw status
numbered** output showing all rules.

![](/assets/img/blog/ufw-firewall-ubuntu/image9.png)

<table>
<tbody>
<tr class="odd">
<td><strong>Q6 (Reflection) Compare your UFW-based approach here to configuring the same policy in pfSense. What does pfSense provide that UFW does not? When would you choose a host-based firewall like UFW over a network-level firewall?</strong></td>
</tr>
<tr class="even">
<td><p>pfSense gives you stateful inspection, traffic shaping, NAT, VPN termination, IDS/IPS integration (Suricata/Snort), a GUI, and visibility across the entire network perimeter from a single pane. UFW gives you none of that -- it is a single-host packet filter with no GUI, no stateful session management beyond basic conntrack, and no centralized visibility.</p>
<p>You choose UFW (or any host-based firewall) when: you need defense-in-depth and cannot trust the network perimeter alone, when a host is multi-homed or cloud-deployed with no upstream firewall, or when you are hardening individual servers against lateral movement inside a network that pfSense already guards</p></td>
</tr>
</tbody>
</table>

  - Assisted students in hardware clinic for the CPU assembly and
    presented Flipper zero hands on presentation.
