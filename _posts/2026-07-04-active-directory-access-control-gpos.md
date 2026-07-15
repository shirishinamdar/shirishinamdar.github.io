---
title: "Building an Active Directory Domain and Enforcing Access Control with GPOs"
date: 2026-07-04 18:00:00 -0500
categories: [Windows, Access Control]
tags: [Active Directory, AD DS, Domain Controller, Group Policy, GPO, Password Policy, PowerShell, Windows Server 2019, DNS, Access Control, Project]
image:
  path: /assets/img/blog/ad-domain-gpo-access-control/image6.png
  alt: "Active Directory Users and Computers showing NetworkAdmin and FinanceOU under hitech.local."
description: Standing up a Windows Server 2019 Active Directory Domain Controller for hitech.local, joining a client to the domain, creating OUs, users, and groups, applying a hardened password policy through Group Policy, and validating the result with PowerShell. Includes the DNS gotcha that breaks domain joins and the token-refresh gotcha that blocks GPO edits.
---

This is an end to end walkthrough of building a small **Active Directory** environment on Windows Server 2019, joining a client to it, structuring the directory with OUs and groups, hardening authentication through a **Group Policy** password policy, and validating the outcome with PowerShell.

The demonstration touches all three legs of access control:

- **Identification** through unique accounts and OUs
- **Authentication** through a hardened password policy
- **Authorization** through group membership

Along the way it covers two failure modes that are easy to hit and useful to understand: an unresolvable domain caused by a missing DNS role, and a blocked GPO edit caused by a stale session token.

---

## Rename Both Machines Before Promotion

Renaming a server after it has been promoted to a Domain Controller requires a full domain rename operation, which is far more disruptive than renaming beforehand. Both machines get renamed first, before any AD roles are installed.

1. Log into the server VM using its default local credentials.
2. Server Manager → Local Server → click the current computer name.
3. Change → set the computer name to `WIN-SRV-DC01`.
4. Reboot when prompted.
5. Log into the client VM and rename it to `WIN-SRV-CLIENT` the same way, then reboot.

---

## Promote the Domain Controller

On `WIN-SRV-DC01`:

1. Server Manager → **Add Roles and Features**.
2. Select **Active Directory Domain Services** and click through the wizard → **Install**.
3. On the Server Roles screen, confirm the **DNS Server** checkbox is also selected.

That DNS step is critical. If DNS Server is not installed alongside AD DS, the domain will exist in Active Directory but will not be resolvable by any other machine, and the client join later will fail with an "AD DC could not be contacted" error.

4. Once installation completes, click the notification flag → **Promote this server to a domain controller**.
5. Choose **Add a new forest**.
6. Root domain name: `hitech.local`.

![Setting the root domain name to hitech.local during forest creation.](/assets/img/blog/ad-domain-gpo-access-control/image1.png)

7. On the Domain Controller Options screen, set a **Directory Services Restore Mode (DSRM)** password. It is required to proceed and is used only for recovery scenarios, not day to day logon.
8. Confirm DNS Server remains checked on this screen as well.
9. Accept the NetBIOS default (`HITECH`), continue through the prerequisite checks, and click **Install**.
10. The server reboots automatically once promotion completes.

![Domain Controller promotion complete, server rebooted under hitech.local.](/assets/img/blog/ad-domain-gpo-access-control/image2.png)

### Verification checkpoint - confirm DNS before touching the client

Before joining the client, open DNS Manager on the DC (Server Manager → Tools → DNS). Expand **Forward Lookup Zones** and confirm `hitech.local` is listed, with `_msdcs`, `_sites`, `_tcp`, and `_udp` subfolders populated. If the zone is missing or empty:

```powershell
ipconfig /registerdns
Restart-Service netlogon
```

Then recheck. Skipping this check is how the client-side "AD DC could not be contacted" error happens.

---

## Join the Client to the Domain

On `WIN-SRV-CLIENT`:

1. Set the client's **Preferred DNS server** to the DC's IP address (find it via `ipconfig` on the DC). Domain join depends entirely on DNS resolution of the domain's SRV records. If the client is still using a DHCP-assigned DNS server, the join will fail even though the domain exists.
2. Confirm resolution works before attempting the join:

```powershell
nslookup hitech.local
```

It should return the DC's IP address with no error.

3. Server Manager → Local Server → click the current domain / workgroup value.
4. Select **Domain**, type `hitech.local`.
5. Authenticate with the DC's local admin credentials.
6. Reboot when the join is confirmed.

![Computer Name and Domain Changes dialog, joining WIN-SRV-CLIENT to hitech.local.](/assets/img/blog/ad-domain-gpo-access-control/image3.png)

![Client network configuration confirming DNS Server is set to the domain controller's IP address.](/assets/img/blog/ad-domain-gpo-access-control/image4.png)

![Domain join confirmation on WIN-SRV-CLIENT.](/assets/img/blog/ad-domain-gpo-access-control/image5.png)

---

## Create Organizational Units, Users, and Groups

Back on `WIN-SRV-DC01`, in Active Directory Users and Computers (Server Manager → Tools → ADUC).

1. Right-click `hitech.local` → **New** → **Organizational Unit** → name it `NetworkAdmin`.
2. Right-click **NetworkAdmin** → **New** → **User**. First name / full name: `IT Head`. Logon name: `IT_Head`.
3. Set the password, check **Password never expires**, and uncheck "User must change password at next logon."
4. Right-click `IT_Head` → **Properties** → **Member Of** tab → **Add** → type `Domain Admins` → add it. Repeat for `Enterprise Admins`.
5. Right-click **NetworkAdmin** → **New** → **Group**. Name: `TechSupport`. Group scope: **Global**. Group type: **Security**.
6. Add `IT_Head` to `TechSupport` the same way the other group memberships were added.
7. Right-click `hitech.local` → **New** → **Organizational Unit** → name it `FinanceOU`.
8. Right-click **FinanceOU** → **New** → **Computer** → name it `Computer01`.

![Active Directory Users and Computers tree, showing NetworkAdmin and FinanceOU under hitech.local.](/assets/img/blog/ad-domain-gpo-access-control/image6.png)

![Adding IT_Head to the TechSupport group via the group's Members tab.](/assets/img/blog/ad-domain-gpo-access-control/image7.png)

![IT_Head user properties, General tab.](/assets/img/blog/ad-domain-gpo-access-control/image8.png)

![IT_Head account options with Password never expires enabled.](/assets/img/blog/ad-domain-gpo-access-control/image9.png)

![IT_Head Member Of tab.](/assets/img/blog/ad-domain-gpo-access-control/image10.png)

![FinanceOU with Computer01 created inside it.](/assets/img/blog/ad-domain-gpo-access-control/image11.png)

![TechSupport group properties confirming Global security scope.](/assets/img/blog/ad-domain-gpo-access-control/image12.png)

### Verification checkpoint - confirm every membership with PowerShell

A first pass through these steps can silently skip a group add if a dialog closes before **Apply** is clicked. Verify with PowerShell rather than trusting the GUI alone:

```powershell
Get-ADOrganizationalUnit -Filter 'Name -like "*"' | Select-Object Name, DistinguishedName
Get-ADPrincipalGroupMembership -Identity IT_Head | Select-Object Name
Get-ADGroup -Identity TechSupport -Properties GroupScope, GroupCategory
Get-ADComputer -Identity Computer01 | Select-Object Name, DistinguishedName
```

`IT_Head`'s group membership should return four groups: Domain Admins, Enterprise Admins, TechSupport, and Domain Users (the last is a default and can be ignored). If Domain Admins or Enterprise Admins is missing, add it directly:

```powershell
Add-ADGroupMember -Identity "Domain Admins" -Members IT_Head
Add-ADGroupMember -Identity "Enterprise Admins" -Members IT_Head
```

---

## Apply the Password Policy via Group Policy

On `WIN-SRV-DC01`, open **Group Policy Management** (Server Manager → Tools → Group Policy Management).

1. Expand **Forest** → **Domains** → `hitech.local`.
2. Right-click **Default Domain Policy** → **Edit**.

### Gotcha - Edit greyed out because of a stale token

If the current session's account doesn't carry Domain Admins in its security token, Group Policy Management correctly blocks the Edit action. `Run as different user` and `runas /user:...` can both fail with error 1385 ("the user has not been granted the requested logon type at this computer") in restricted environments.

The fix is to elevate the current account, then get a fresh session so the new group membership actually ends up in the token:

```powershell
Add-ADGroupMember -Identity "Domain Admins" -Members <your-account>
Add-ADGroupMember -Identity "Enterprise Admins" -Members <your-account>
gpupdate /force
```

Group membership changes are not reflected in an already-open session's security token. Log off completely and log back in with the same credentials so the token is reissued. Confirm before retrying GPMC:

```powershell
whoami /groups | findstr "Admins"
```

Once **Domain Admins** appears in that output, **Default Domain Policy → Edit** opens normally.

### The Password Policy

In the Group Policy Management Editor:

**Computer Configuration → Policies → Windows Settings → Security Settings → Account Policies → Password Policy**

| Setting                                    | Value              |
| ------------------------------------------ | ------------------ |
| Minimum Password Length                    | 12 characters      |
| Maximum Password Age                       | 90 days            |
| Minimum Password Age                       | 1 day              |
| Enforce Password History                   | 20 remembered      |
| Store passwords using reversible encryption| Disabled           |

Close the editor and force the policy to apply immediately:

```powershell
gpupdate /force
```

---

## Validate the Configuration

On `WIN-SRV-DC01`, open PowerShell as administrator:

```powershell
Get-ADUser -Identity IT_Head -Properties *
Get-ADComputer -Filter * | Out-File C:\useraccounts.txt
gpresult /H C:\passwords-policy-settings.html
```

Open `passwords-policy-settings.html` in a browser once, before treating it as done, to confirm the report actually rendered the password policy values rather than an empty or malformed page. This is a silent failure mode worth checking every time.

---

## What This Actually Demonstrates

The point of the exercise isn't the specific values in the password policy, it's that access control is a **chain** of three things, and the chain breaks the moment any link is weak.

**Identification** was established the moment `IT_Head` was created as a distinct account with a unique logon name inside the `NetworkAdmin` OU. The directory now has an unambiguous record of who this identity is and where it lives organizationally.

**Authentication** was enforced through the Default Domain Policy password settings. A 12-character minimum length, a 90-day maximum age, a 1-day minimum age (preventing rapid password cycling to defeat history requirements), 20 remembered passwords, and disabled reversible encryption together raise the cost of credential compromise and close off a known weak point in how Windows can optionally store passwords.

**Authorization** was expressed through group membership. Placing `IT_Head` in `Domain Admins`, `Enterprise Admins`, and `TechSupport` did not just label the account, it granted it the specific rights those groups carry, which is the practical mechanism by which access control decisions actually get enforced at logon and resource access time.

The most instructive part of the exercise was the troubleshooting, because each failure traced back to a genuine access control concept rather than a random glitch.

The client's initial failure to join the domain ("AD DC for `hitech.local` could not be contacted") came down to the DNS Server role being unchecked during promotion. That is a reminder that identification and authentication depend on a working directory lookup mechanism (DNS/SRV records) before any credential is even checked.

Later, Group Policy Management refused to let the Default Domain Policy be edited. That turned out to be authorization working exactly as designed: the logged in session simply did not carry Domain Admins rights in its token, so the system correctly denied the action rather than trusting the account's name alone. The fix, adding the account to the right group and then forcing a fresh logon so the token actually reflected that membership, was itself a small demonstration of why authorization is evaluated at logon time, not continuously re-checked against live group membership.

An identity must be established, that identity must be authenticated against a policy strong enough to resist compromise, and only then does authorization determine what that authenticated identity is actually permitted to do. Weakness or misconfiguration at any one link, an unresolvable domain name, a missing role, a stale session token, breaks the whole chain even when the other two links are configured correctly.
