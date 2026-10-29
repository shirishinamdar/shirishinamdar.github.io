---
title: "Building a Shuffle SOAR IP-Enrichment Playbook with VirusTotal, From Install to Interactive Form"
date: 2026-10-24 18:00:00 -0500
categories: [SOAR, Security Automation]
tags: [Shuffle, SOAR, VirusTotal, Docker, OpenSearch, Webhook, Playbook, Linux Mint, Incident Response, vSOC, Project]
description: An end-to-end Shuffle SOAR build on a single Linux Mint VM, installing Docker, deploying the Shuffle stack, and building a webhook-triggered playbook that checks an alert's IP against VirusTotal and labels it Malicious or Clean. Tested with a clean and a known-bad IP, then exposed as an interactive web form.
image:
  path: /assets/img/blog/shuffle-soar-ip-enrichment/image30.png
  alt: "Shuffle IP Reputation Check form returning ALERT: 118.37.214.187 flagged by 12 engines."
---

This is a complete walkthrough of building a **Shuffle SOAR** playbook from nothing: install Docker on a Linux Mint VM, deploy the Shuffle stack, and build an **alert-enrichment playbook** that checks an alert's source IP against **VirusTotal** and labels it **Malicious** or **Clean**. It finishes by testing both outcomes with `curl` and exposing the playbook as a simple web form.

## What is Shuffle?

Shuffle is an open-source **SOAR** (Security Orchestration, Automation and Response) platform that automates repetitive security tasks and incident-response workflows. It integrates with tools such as Wazuh, SIEM platforms, threat-intelligence feeds, and endpoint security products to collect alerts, enrich events, and trigger automated actions. In a virtual SOC it cuts manual analyst work and speeds up response.

**The playbook we build:**

```text
Webhook (alert in) -> ReceiveAlert -> VirusTotal IP lookup -> Malicious? / Clean?
```

---

# Part 1: Prepare the VM

## Update the System and Install Base Tools

```bash
sudo apt update && sudo apt -y upgrade
sudo apt -y install ca-certificates curl gnupg git
```

## Check Available Memory

OpenSearch, Shuffle's database, is the heaviest component, so confirm the RAM before installing.

```bash
free -h
```

![free -h showing 7.7 GiB of RAM and 2.8 GiB of swap.](/assets/img/blog/shuffle-soar-ip-enrichment/image1.png)

---

# Part 2: Install Docker

Shuffle runs as a set of containers. One Mint-specific detail: Docker's apt repository uses **Ubuntu** codenames, so the repo line below uses `UBUNTU_CODENAME` instead of Mint's own codename.

## Remove Old Docker Packages

```bash
sudo apt -y remove docker.io docker-compose podman-docker containerd runc
```

## Add Docker's Signing Key and Repository

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list
```

## Install Docker Engine and Compose

```bash
sudo apt update
sudo apt -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## Allow Docker Without sudo and Verify

```bash
sudo usermod -aG docker $USER
newgrp docker
docker --version
docker compose version
docker run --rm hello-world
```

This gave **Docker Engine 29.9.1** and **Compose v5.6.0**, and `hello-world` confirms Docker is working.

![hello-world output confirming the Docker installation works.](/assets/img/blog/shuffle-soar-ip-enrichment/image2.png)

---

# Part 3: Deploy Shuffle

## Download Shuffle

```bash
cd ~
git clone https://github.com/Shuffle/Shuffle
cd Shuffle
```

## Prepare the Host for OpenSearch

OpenSearch needs three host settings: its data folder owned by UID 1000, swap disabled, and a higher memory-map limit (persisted across reboots).

```bash
mkdir -p shuffle-database
sudo chown -R 1000:1000 shuffle-database
sudo swapoff -a
sudo sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" | sudo tee /etc/sysctl.d/99-shuffle.conf
```

## Start the Stack

```bash
docker compose up -d
```

The repository clones, the OpenSearch prerequisites are applied, and the image pull starts.

![Repository cloned, OpenSearch prerequisites applied, and the image pull started.](/assets/img/blog/shuffle-soar-ip-enrichment/image3.png)

Once the images are pulled, all five containers start.

![All Shuffle images pulled and the five containers started.](/assets/img/blog/shuffle-soar-ip-enrichment/image4.png)

## Verify the Containers

```bash
docker compose ps
```

`backend`, `frontend`, `opensearch`, `orborus`, and `security` all show **Up**. The frontend is published on port `3001`.

![docker compose ps showing the five Shuffle containers running.](/assets/img/blog/shuffle-soar-ip-enrichment/image5.png)

## Create the Admin Account

Browse to `http://localhost:3001` and register the first administrator account.

![Create administrator account page showing a successful registration.](/assets/img/blog/shuffle-soar-ip-enrichment/image6.png)

After logging in, the core apps (**Http** and **Shuffle Tools**) are loaded, which confirms the platform works.

![Org Apps page with Http and Shuffle Tools loaded.](/assets/img/blog/shuffle-soar-ip-enrichment/image7.png)

---

# Part 4: Start Shuffle After a Reboot

OpenSearch needs swap off and the higher memory-map limit every time the VM starts, and it must finish starting before the backend can connect.

```bash
cd ~/Shuffle
sudo swapoff -a
sudo sysctl -w vm.max_map_count=262144
docker compose up -d
```

**Wait about 3 minutes**, then check the containers.

```bash
docker compose ps
```

![docker compose ps after a restart, with all five containers up.](/assets/img/blog/shuffle-soar-ip-enrichment/image8.png)

Confirm the platform is healthy:

```bash
curl -s http://localhost:3001/api/v1/health
```

> **Checkpoint:** the reply starts with `"success":true`. An OpenSearch status of **yellow** is normal on a single-node lab.
{: .prompt-tip }

---

# Part 5: Log In and Create the Workflow

Open a Firefox private window, go to `http://localhost:3001/login`, and sign in with the admin account.

On the welcome screen, choose **Continue with Shuffle Core**, the manual workflow builder.

![Shuffle onboarding, choosing Continue with Shuffle Core.](/assets/img/blog/shuffle-soar-ip-enrichment/image9.png)

In the left menu, go to **Automate > Apps**, search **VirusTotal**, and activate **VirusTotal v3**.

Then go to **Workflows > My Workflows** and click **+ Create Workflow**. Name it `IP-Enrichment`.

![The empty My Workflows page with the Create Workflow button.](/assets/img/blog/shuffle-soar-ip-enrichment/image10.png)

---

# Part 6: Build the Playbook

The first three nodes receive the alert and enrich its IP with VirusTotal.

## Webhook Trigger

From **Triggers**, drag **Webhook** onto the canvas and connect it to the start node. Click the webhook and press **Start**. Copy its URL, then replace `localhost` with the VM's IP so other machines can reach it, for example:

```text
http://192.168.192.129:3001/api/v1/hooks/webhook_<id>
```

## ReceiveAlert Node

Click the default start node (labelled *Change Me*). Rename it **ReceiveAlert**, keep the action **Repeat back to me**, and set **Call** to `$exec`. This echoes the incoming alert so it shows in every run.

## VirusTotal Node

From **Your Apps**, drag **Virustotal v3** onto the canvas and connect ReceiveAlert to it.

![Webhook, ReceiveAlert and a Virustotal v3 node on the canvas.](/assets/img/blog/shuffle-soar-ip-enrichment/image11.png)

In the **Setup** tab, rename the node `VirusTotal` and select your VirusTotal authentication. **The name matters**: Shuffle builds the variable `$virustotal` from it.

![VirusTotal node Setup tab, renamed with authentication attached.](/assets/img/blog/shuffle-soar-ip-enrichment/image12.png)

In the **Configuration** tab, choose **Get an ip address report** and set the **Ip** field to `$exec.src_ip`. Save.

![VirusTotal node configured to look up $exec.src_ip.](/assets/img/blog/shuffle-soar-ip-enrichment/image13.png)

> The free VirusTotal API key is licensed for personal, non-commercial use. Use a properly licensed key before running this in a production environment.
{: .prompt-warning }

---

# Part 7: Add the Malicious and Clean Branches

VirusTotal returns how many security engines flag the IP. The playbook branches on that number: **1 or more is Malicious, 0 is Clean.**

## Branch Nodes

Drag a **Shuffle Tools** node to the left of VirusTotal. In **Setup**, name it `Malicious`. In **Configuration**, choose **Repeat back to me** and set **Call** to:

```text
ALERT: $exec.src_ip flagged by $virustotal.body.data.attributes.last_analysis_stats.malicious engines
```

![The Malicious node's Call field, using the VirusTotal malicious-engine count.](/assets/img/blog/shuffle-soar-ip-enrichment/image14.png)

Drag a second **Shuffle Tools** node to the right. Name it `Clean`, choose **Repeat back to me**, and set **Call** to:

```text
INFO: $exec.src_ip clean
```

Hover over VirusTotal and drag from its blue dot onto each branch node.

![VirusTotal connected to a branch node on each side.](/assets/img/blog/shuffle-soar-ip-enrichment/image15.png)

## Conditions

Click the line from VirusTotal to **Malicious**, then **New condition**.

![The Conditions panel for the branch, with the New condition button.](/assets/img/blog/shuffle-soar-ip-enrichment/image16.png)

Fill it in and click **Submit**:

| Branch | Source | Condition | Destination |
|---|---|---|---|
| Malicious | `$virustotal.body.data.attributes.last_analysis_stats.malicious` | larger than | `0` |
| Clean | the same variable | equals | `0` |

![The Malicious branch condition, larger than 0.](/assets/img/blog/shuffle-soar-ip-enrichment/image17.png)

Repeat on the line to **Clean** with **equals** `0`.

![The Clean branch condition, equals 0.](/assets/img/blog/shuffle-soar-ip-enrichment/image18.png)

Save with `Ctrl + S`. Each branch line now shows **1 condition**.

![The finished workflow with a condition on each branch.](/assets/img/blog/shuffle-soar-ip-enrichment/image19.png)

---

# Part 8: Test the Playbook

The same command works for any IP, just change the `src_ip` value and send it again.

## Test 1: Clean IP

Save the webhook URL in the terminal, then send a simulated alert with `curl`:

```bash
WEBHOOK="http://192.168.192.129:3001/api/v1/hooks/webhook_<id>"
curl -s -X POST "$WEBHOOK" -H "Content-Type: application/json" \
  -d '{"alert":"Outbound connection","src_ip":"8.8.8.8","host":"ws-01"}'
```

> **Checkpoint:** the reply is `{"success": true, "execution_id": "..."}`.
{: .prompt-tip }

![curl posting a simulated alert for 8.8.8.8 and receiving success: true.](/assets/img/blog/shuffle-soar-ip-enrichment/image20.png)

In the workflow, click **Debug** and open the newest run. The run ends at **Clean**.

![Debug view, Clean node result: INFO: 8.8.8.8 clean.](/assets/img/blog/shuffle-soar-ip-enrichment/image21.png)

## Test 2: Known-Bad IP

Pick a recently reported IP from [AbuseIPDB](https://www.abuseipdb.com) with a high confidence score. This lab used `193.32.162.84`, which had a **100%** abuse confidence score.

![AbuseIPDB showing 193.32.162.84 with a 100% abuse confidence score.](/assets/img/blog/shuffle-soar-ip-enrichment/image22.png)

Wait about a minute, then send it:

```bash
curl -s -X POST "$WEBHOOK" -H "Content-Type: application/json" \
  -d '{"alert":"Outbound connection","src_ip":"193.32.162.84","host":"ws-01"}'
```

![curl posting the simulated alert for 193.32.162.84.](/assets/img/blog/shuffle-soar-ip-enrichment/image23.png)

Open the newest run in **Debug**. The alert arrived in `$exec`...

![Debug view showing the incoming alert with src_ip 193.32.162.84.](/assets/img/blog/shuffle-soar-ip-enrichment/image24.png)

...VirusTotal returned **status 200** for the IP...

![The VirusTotal node result, status 200 for ip_address 193.32.162.84.](/assets/img/blog/shuffle-soar-ip-enrichment/image25.png)

...and the run took the **Malicious** branch: `ALERT: 193.32.162.84 flagged by 14 engines`.

![The Malicious node result, flagged by 14 engines.](/assets/img/blog/shuffle-soar-ip-enrichment/image26.png)

> The lookup only queries VirusTotal. Nothing on the VM connects to the bad IP, so the test is safe.
{: .prompt-info }

---

# Part 9: An Interactive IP-Check Form

Shuffle can run the same playbook as a web form: type an IP, click **Run workflow**, and the verdict appears on the page. The form shows the output of the **last node that runs**, so the Malicious or Clean message is the result.

1. In the workflow editor, click the **pencil icon** next to the workflow name to open **Form Control**.
2. Under **Input fields**, add one row with the label `IP Address` and the JSON key `src_ip`. The key keeps `$exec.src_ip` working in every node.

![Form Control, adding the src_ip input field.](/assets/img/blog/shuffle-soar-ip-enrichment/image27.png)

3. Under **Input Markdown**, add the text shown at the top of the form:

```markdown
## IP Reputation Check
Enter an IP address to check it against VirusTotal.
The SOAR playbook will classify it as **Clean** or **Malicious**.
```

4. Save the settings, then save the workflow with `Ctrl + S`.
5. Go to **Workflows > Org Forms** and open **IP-Enrichment**.

![Org Forms listing the IP-Enrichment form.](/assets/img/blog/shuffle-soar-ip-enrichment/image28.png)

![The IP Reputation Check form with an IP Address field and Run workflow button.](/assets/img/blog/shuffle-soar-ip-enrichment/image29.png)

Type an IP and click **Run workflow**. In this test, `118.37.214.187` was flagged by **12 engines**.

![The form result: ALERT: 118.37.214.187 flagged by 12 engines.](/assets/img/blog/shuffle-soar-ip-enrichment/image30.png)

---

## Takeaways

- **Node names become variables.** Naming the node `VirusTotal` is what produces `$virustotal`, so the branch conditions and messages depend on it.
- **One counter drives the decision.** `last_analysis_stats.malicious` is enough for a first-pass verdict: `0` is Clean, anything higher is Malicious.
- **Always re-apply the OpenSearch host settings after a reboot,** and give the backend about three minutes before testing.
- **Test both outcomes.** A clean IP (`8.8.8.8`) and a known-bad one prove each branch actually fires.

## Where This Goes Next

In a SOC, the same webhook receives alerts from tools like **Wazuh**, and each suspicious IP is checked against VirusTotal and labelled automatically. Next steps for the playbook:

- Replace the Clean/Malicious messages with a real notification (email or Teams).
- Feed the webhook from live Wazuh alerts instead of `curl`.
- Turn confirmed findings into follow-up actions such as ticketing or a firewall block.
