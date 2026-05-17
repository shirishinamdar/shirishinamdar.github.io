---
title: "UFW Host-Based Firewall on Kali Linux"
date: 2026-05-09 18:54:00 -0400
categories: [Network Security, Firewalls]
tags: [UFW, Firewall, iptables, Kali Linux, Endpoint Hardening, Project]
description: Installing UFW on Kali Linux, setting a default-deny ingress policy, allowing specific services, and confirming how the friendly UFW syntax maps down to the iptables INPUT chain underneath.
image:
  path: /assets/img/blog/ufw-firewall-ubuntu/image1.png
  alt: "Verifying the installed UFW version on Kali Linux."
---

UFW exists because `iptables` is powerful but unreadable. If you've ever stared at a chain of `-A INPUT -p tcp --dport 22 -j ACCEPT` rules and wished they read like English, UFW is the answer — a frontend that compiles `ufw allow ssh` down to the same kernel firewall rule, just without the line noise.

This post is my walkthrough of setting up UFW on Kali Linux as a host-based firewall: enforcing default-deny ingress, writing explicit allow rules for the services I actually want exposed, and confirming each friendly command translates into the underlying `iptables` chain I expect.

---

## Background: Where UFW Sits

Linux firewalls live in the kernel's `netfilter` framework. The kernel exposes that framework through a series of command-line tools, each layered on top of the last:

| Layer | Tool | Audience |
| --- | --- | --- |
| Kernel hooks | `netfilter` | n/a (in-kernel) |
| Rule engine, low level | `iptables` / `nftables` | Skilled administrators |
| Friendly frontend | `ufw` | Day-to-day endpoint hardening |
| Web/GUI frontends | `gufw`, distro firewall apps | End users |

Every UFW command ultimately writes one or more rules into the `iptables` INPUT, OUTPUT, or FORWARD chain. `ufw status verbose` and `ufw show added` will both reveal those rules. For anyone already comfortable with `iptables`, UFW is essentially a smaller language that compiles to the same target — useful when the operational goal is "deny everything inbound except SSH on a known port and HTTPS on 443," and not "build a custom rate-limited reverse-path-checking forwarding chain."

This project focuses on UFW's most important job for an endpoint: implementing the **principle of least privilege** at the network layer. Anything not explicitly permitted should be dropped.

---

## Project Setup

| Item | Detail |
| --- | --- |
| Host OS | Kali Linux (rolling) |
| Package source | Default Kali apt repository |
| Firewall scope | Host-based (single VM, no second machine required) |
| Test traffic | Simulated locally with `netcat` on the loopback interface |
| Privilege | All commands require root (`sudo su` or `sudo <cmd>`) |

UFW does not ship enabled on Kali. That is the correct default: enabling a firewall without first reviewing the rule set on a remote host is a fast way to lock yourself out.

---

## 1. Installing UFW and Checking Version

```bash
sudo apt update
sudo apt install ufw -y
ufw version
```

`ufw version` confirms the package is installed and prints the active version string.

![Verifying the installed UFW version after apt install.](/assets/img/blog/ufw-firewall-ubuntu/image1.png)

---

## 2. Verifying the Default Status Before Touching Anything

```bash
sudo ufw status verbose
```

Expected output on a fresh install: `Status: inactive`. Checking status before enabling matters — the only safe time to review the rule set is *before* the firewall is live and dropping packets.

![ufw status verbose on a fresh install — status: inactive.](/assets/img/blog/ufw-firewall-ubuntu/image2.png)

---

## 3. Setting the Default Policies

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

These two commands set the baseline behavior:

- **Deny incoming** — any inbound packet that does not match an explicit allow rule is dropped at the end of the INPUT chain.
- **Allow outgoing** — outbound traffic initiated from the host (DNS, software updates, normal application traffic) is permitted unless a later rule restricts it.

A default-allow ingress policy means any service the host accidentally starts is immediately reachable from any source. A default-deny ingress policy inverts that assumption: nothing is reachable until you say so. For host hardening this is the only correct default.

---

## 4. Enabling UFW

```bash
sudo ufw enable
```

UFW prints a warning that this command may disrupt existing SSH connections. On a remote host that is a real concern; on a local VM with console access it is safe. The kernel hooks are installed and the firewall is now enforcing the rule set.

```bash
sudo ufw status verbose
```

The status output now shows `Status: active`, the two default policies, and any currently configured rules (none yet, in this project's first pass).

![UFW enabled with default deny incoming / allow outgoing policies.](/assets/img/blog/ufw-firewall-ubuntu/image3.png)

A packet that arrives on the INPUT chain and matches no UFW-authored rule falls through to the default policy at the end of the chain — and is dropped. `sudo ufw show raw` exposes the actual `iptables` rules in their compiled form, including the terminal `ufw-user-input` jump and the default policy target.

---

## 5. Allowing a Service: SSH on Port 22

The first hole in the default-deny posture is the one that lets administration continue:

```bash
sudo ufw allow ssh
```

UFW recognizes a number of named services (`ssh`, `http`, `https`, `smtp`, etc.) by reading `/etc/services`. The command above is equivalent to:

```bash
sudo ufw allow 22/tcp
```

Both forms compile to the same `iptables` rule.

![UFW allow rule for SSH, visible in ufw status output.](/assets/img/blog/ufw-firewall-ubuntu/image4.png)

---

## 6. Allowing Specific Ports

For services without a `/etc/services` name, or to be explicit about the protocol, port-based rules are written directly:

```bash
sudo ufw allow 443/tcp        # HTTPS
sudo ufw allow 53/udp         # DNS to a local resolver
```

Each rule is added to the **end** of the user-defined chain in evaluation order. Order matters when allow and deny rules overlap.

![Adding additional allow rules for HTTPS and DNS.](/assets/img/blog/ufw-firewall-ubuntu/image5.png)

---

## 7. Source-Restricted Rules

The principle of least privilege scales further — instead of allowing a port from anywhere, the rule can be restricted to a specific source IP or subnet:

```bash
sudo ufw allow from 192.168.150.0/24 to any port 22 proto tcp
```

This permits SSH only from the project subnet. Anything else hitting port 22 still meets the default deny.

![Source-restricted SSH allow rule limiting access to the project subnet.](/assets/img/blog/ufw-firewall-ubuntu/image6.png)

---

## 8. Mapping UFW Commands to iptables

Two commands make the connection between UFW's friendly syntax and what the kernel actually enforces:

```bash
sudo ufw show added       # the commands UFW would re-issue to rebuild current state
sudo iptables -L -n -v    # the live iptables rule set, no DNS resolution
```

`iptables -L` shows the actual chains (`INPUT`, `FORWARD`, `OUTPUT`) plus UFW's bookkeeping chains (`ufw-before-input`, `ufw-after-input`, `ufw-user-input`, etc). Reading them confirms that an `ufw allow 22/tcp` produced a real `ACCEPT` line in `ufw-user-input` and the eventual fallthrough drops live in `ufw-after-input`.

![iptables -L output showing UFW's compiled rule chains.](/assets/img/blog/ufw-firewall-ubuntu/image7.png)

---

## 9. Logging

```bash
sudo ufw logging on
sudo tail -F /var/log/ufw.log
```

UFW logs every blocked packet to `/var/log/ufw.log` (also surfaced through `dmesg` and the `kern.log` channel depending on rsyslog configuration). Each log line includes timestamp, interface, source/destination IPs and ports, and the reason — `[UFW BLOCK]`, `[UFW ALLOW]`, or `[UFW AUDIT]`.

![UFW logging entries in /var/log/ufw.log capturing blocked traffic.](/assets/img/blog/ufw-firewall-ubuntu/image8.png)

Log volume scales with the noisiness of the network. On an internet-exposed host this fills disk quickly; production deployments either rate-limit logging (`ufw logging low`) or forward the log to a remote collector and rotate aggressively.

---

## 10. Testing the Rule Set

Two quick verifications confirm the firewall is behaving:

```bash
# From the host, against itself — should succeed for allowed ports
nc -zv 127.0.0.1 22

# Against a closed port — should fail with the connection refused / filtered
nc -zv 127.0.0.1 12345
```

The successful connection on 22 and the timeout on the unbound port together prove that the allow rule and the default deny are both in effect.

![Netcat test confirming allowed and blocked behavior end to end.](/assets/img/blog/ufw-firewall-ubuntu/image9.png)

---

## Key Observations

- **Default-deny is the only sensible ingress posture for an endpoint.** A default-allow posture means every accidentally-started service is exposed; default-deny means nothing is reachable unless you've signed off on it.
- **UFW is a frontend, not a different firewall.** Every rule it issues lands in `iptables` chains the kernel was going to enforce anyway. Anyone fluent in `iptables` can read UFW's output and verify the actual posture.
- **Order matters when allow and deny rules overlap.** Rules in UFW are evaluated top to bottom inside `ufw-user-input`. `ufw insert <n> ...` is useful for placing a deny rule above a broader allow.
- **Service names are convenient but opaque.** `ufw allow http` is shorter than `ufw allow 80/tcp`, but a port-and-protocol rule is unambiguous and survives changes to `/etc/services`. In a hardened deployment the explicit form is worth the extra characters.
- **Logging is a separate decision from policy.** A correctly configured firewall can be silent or noisy depending on whether logging is enabled, and noisy is usually better in the first weeks of a new posture so you can see what was being denied that you didn't expect.

---

## Where This Sits in the Stack

The previous post in this project series covered **pfSense** at the network perimeter — the firewall that controls what enters and leaves the subnet. UFW is the second layer: it controls what reaches each individual host even if the perimeter has already passed the traffic through. The next post wires both layers' logs (along with Cowrie, Snort, and Tripwire alerts) into a centralized **Graylog** SIEM so that drops, allows, and detections can be correlated across the whole stack.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           