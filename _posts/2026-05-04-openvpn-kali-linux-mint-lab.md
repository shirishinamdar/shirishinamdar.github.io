---
title: "Building an OpenVPN Tunnel Between Kali and Linux Mint"
date: 2026-05-04 01:30:39 -0400
categories: [Networking, Offensive Security]
tags: [OpenVPN, VPN, PKI, Kali Linux, Linux Mint, VMware, Networking, Lab]
description: Step-by-step build of a working OpenVPN tunnel between two VMware VMs (Kali server, Linux Mint client), covering PKI setup, certificate generation, server.conf, client.ovpn, and end-to-end ping verification.
image:
  path: /assets/img/blog/openvpn-kali-linux-mint-lab/cover.svg
  alt: "OPENVPN — Encrypted Tunnel · Kali ↔ Linux Mint"
---
## Overview
This week focused on setting up a working OpenVPN tunnel between two
Linux VMs in VMware - Kali Linux as the server and Linux Mint as the
client, both running on a NAT network. The lab covered PKI setup,
certificate generation, server and client configuration, file transfer,
and verifying the encrypted tunnel with a ping test.

OpenVPN is an open-source tool that creates a secure, encrypted tunnel
between two machines over a network. A VPN tunnel means all traffic
between the two machines is encrypted

## OpenVPN Lab - Kali (Server) + Linux Mint (client)
## Environment - VMware NAT
Both VMs were set up on VMware with NAT networking so they can
communicate on the same subnet.

**Server (Kali Linux): 192.168.147.131**

**Client (Linux Mint (client)): 192.168.147.130**

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image1.jpeg)

*Figure 1 - Linux Mint (client) VM (client) running in VMware.*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image2.jpeg)

*Figure 2 - Kali Linux VM (server) running in VMware.*

## Step 1 - Install OpenVPN & Easy-RSA on Both Machines
Ran apt update and upgrade on both machines, then installed openvpn and
easy-rsa.

easy-rsa is a tool that helps create and manage certificates. Think of
certificates like digital ID cards - they prove that the machine
connecting to the VPN is actually who it claims to be.

**\#sudo apt-get update && sudo apt-get upgrade**

**\#apt update && apt install -y openvpn easy-rsa**

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image3.jpeg)

*Figure 3 - apt update running on Kali.*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image4.jpeg)

*Figure 4 - apt update running on Linux Mint (client).*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image5.jpeg)

*Figure 5 - OpenVPN and Easy-RSA installation completed.*

## Step 2 - Build the PKI on the Server (Kali)
Set up the certificate authority, generated server cert, DH parameters,
and TLS auth key.

**\#make-cadir \~/openvpn-ca && cd \~/openvpn-ca**

**./easyrsa init-pki**

**./easyrsa build-ca nopass**

**./easyrsa gen-req server nopass**

**./easyrsa sign-req server server**

**./easyrsa gen-dh**

**openvpn --genkey secret ta.key**

Note: At prompts for server/client name: just hit Enter. When asked to
confirm details: type yes.

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image6.jpeg)

*Figure 6 - PKI initialized and CA built on Kali.*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image7.jpeg)

*Figure 7 - Server certificate signed and DH parameters generated.*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image8.jpeg)

*Figure 8 - TLS auth key generated.*

## Step 3 - Generate Client Certificate
Generated a separate certificate for the client machine. Each device
that connects to the VPN needs its own certificate.

**\#./easyrsa gen-req client1 nopass**

**\#./easyrsa sign-req client client1**

Note: At prompts: hit Enter for name, type **yes** to confirm.

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image9.jpeg)

*Figure 9 - client1 certificate request and signing completed.*

## Step 4 - Create server.conf on Kali
Created /etc/openvpn/server.conf with the server settings. This file
tells OpenVPN where to find the certificates, which port to listen on,
what IP range to give to VPN clients, and what encryption to use.

**\#nano /etc/openvpn/server.conf**

**port 1194**

**proto udp**

**dev tun**

**ca /root/openvpn-ca/pki/ca.crt**

**cert /root/openvpn-ca/pki/issued/server.crt**

**key /root/openvpn-ca/pki/private/server.key**

**dh /root/openvpn-ca/pki/dh.pem**

**tls-auth /root/openvpn-ca/ta.key 0**

**server 10.8.0.0 255.255.255.0**

**keepalive 10 120**

**cipher AES-256-CBC**

**persist-key**

**persist-tun**

**status /var/log/openvpn-status.log**

**verb 3**

Save and exit with Ctrl+X, then Y.

Port 1194 UDP is the default OpenVPN port. The server 10.8.0.0 line
means VPN clients will get IP addresses in the 10.8.0.x range - this is
a virtual subnet separate from the physical network. AES-256-CBC is the
encryption algorithm - it is the same standard used by banks and
governments.

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image10.jpeg)

*Figure 10 - server.conf saved in nano on Kali.*

## Step 5 - Enable IP Forwarding & Start OpenVPN Server
IP forwarding allows the server to pass traffic between the VPN tunnel
and the regular network. Without this, packets coming in through the VPN
have nowhere to go.

**\#echo 'net.ipv4.ip\_forward=1' | sudo tee -a /etc/sysctl.conf**

**sudo sysctl -p**

**sudo systemctl start openvpn@server**

**sudo systemctl enable openvpn@server**

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image11.jpeg)

*Figure 11 - IP forwarding enabled and OpenVPN server service started.*

## Step 6 - Transfer Certificates from Kali to Linux Mint (client)
The client machine needs a copy of the CA cert, its own certificate, its
private key, and the ta.key. These were served from Kali using Python's
built-in HTTP server and downloaded on Linux Mint (client) through the
browser.

This is a common quick method for transferring files between two
machines on the same network - Python starts a temporary web server in
whatever folder you run it from, and the other machine downloads from it
like any website. In a real environment you would use SCP or a more
secure method.

**\#cd /tmp**

**cp /root/openvpn-ca/pki/ca.crt .**

**cp /root/openvpn-ca/pki/issued/client1.crt .**

**cp /root/openvpn-ca/pki/private/client1.key .**

**cp /root/openvpn-ca/ta.key .**

**python3 -m http.server 8080**

On Linux Mint (client), open a browser and go to
http://192.168.147.131:8080 - download all 4 files and save them to
/home/osboxes/.

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image12.jpeg)

*Figure 12 - Files staged in /tmp and Python HTTP server running on
Kali.*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image13.jpeg)

*Figure 13 - Linux Mint (client) browser downloading certificate files
from Kali's HTTP server.*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image14.jpeg)

*Figure 14 - Certificate files downloaded to Linux Mint (client).*

## Step 7 - Create client.ovpn on Linux Mint (client)
Created the client config file on Linux Mint (client). This tells OpenVPN
on the client side where the server is, which certs to use, and what
settings to match the server with.

**\#nano /home/osboxes/client.ovpn**

**client**

**dev tun**

**proto udp**

**remote 192.168.147.131 1194**

**resolv-retry infinite**

**nobind**

**ca ca.crt**

**cert client1.crt**

**key client1.key**

**tls-auth ta.key 1**

**cipher AES-256-CBC**

**verb 3**

The remote line points to the Kali server IP and port. The tls-auth line
uses 1 on the client side (vs 0 on the server) - this is just how
OpenVPN distinguishes which end is which for the TLS key.

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image15.jpeg)

*Figure 15 - client.ovpn file created on Linux Mint (client).*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image16.jpeg)

*Figure 16 - client.ovpn contents verified in terminal.*

## Step 8 - Connect & Verify the VPN Tunnel
Ran openvpn on Linux Mint (client) with the client config. The tunnel
came up and Linux Mint (client) was assigned VPN IP 10.8.0.2 by the
server.

**\#sudo openvpn --config client.ovpn**

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image17.jpeg)

*Figure 17 - OpenVPN connecting on Linux Mint (client), handshake and
certificate verification in progress.*

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image18.jpeg)

*Figure 18 - Tunnel up: VERIFY OK, Peer Connection Initiated, Linux
Mint (client) assigned 10.8.0.2, AES-256-GCM active.*

## Test - Ping Through the VPN
Pinged Kali's VPN IP (10.8.0.1) from Linux Mint (client) to confirm the
encrypted tunnel is working in both directions.

When Linux Mint (client) pings 10.8.0.1, it recognizes that IP belongs to
the VPN tunnel and hands the packet to OpenVPN. OpenVPN encrypts it and
sends it over the physical network to Kali. Kali decrypts it, responds,
and sends an encrypted reply back. Getting replies means the tunnel is
up, authentication worked, and encryption is running in both directions.

**\#ping 10.8.0.1**

![](/assets/img/blog/openvpn-kali-linux-mint-lab/image19.jpeg)

*Figure 19 - Successful ping to 10.8.0.1 confirming the VPN tunnel is
live and encryption is working.*
