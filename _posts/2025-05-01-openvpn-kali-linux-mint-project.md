---
title: "OpenVPN Tunnel Between Kali (Server) and Linux Mint (Client)"
date: 2025-05-01 18:00:00 -0500
categories: [Networking, VPN]
tags: [OpenVPN, PKI, Easy-RSA, Kali Linux, Linux Mint, VMware, Project]
description: Setting up a working OpenVPN tunnel between two Linux VMs in VMware — Kali Linux as the server and Linux Mint as the client. PKI setup, certificate generation, server and client configuration, file transfer, and verifying the encrypted tunnel with a ping test.
image:
  path: /assets/img/blog/openvpn-kali-linux-mint-project/image18.jpeg
  alt: "OpenVPN tunnel up: VERIFY OK, peer connection initiated, AES-256-GCM active."
---

This project focused on setting up a working OpenVPN tunnel between two Linux VMs in VMware — Kali Linux as the server and Linux Mint as the client, both running on a NAT network. It covered PKI setup, certificate generation, server and client configuration, file transfer, and verifying the encrypted tunnel with a ping test.

OpenVPN is an open-source tool that creates a secure, encrypted tunnel between two machines over a network. A VPN tunnel means all traffic between the two machines is encrypted.

---

## OpenVPN Project — Kali (Server) + Linux Mint (Client)

**Environment — VMware NAT.** Both VMs were set up on VMware with NAT networking so they can communicate on the same subnet.

- **Server (Kali Linux):** `192.168.147.131`
- **Client (Linux Mint):** `192.168.147.130`

![Linux Mint VM (client) running in VMware.](/assets/img/blog/openvpn-kali-linux-mint-project/image1.jpeg)

![Kali Linux VM (server) running in VMware.](/assets/img/blog/openvpn-kali-linux-mint-project/image2.jpeg)

---

## Step 1 — Install OpenVPN & Easy-RSA on Both Machines

Ran `apt update` and `upgrade` on both machines, then installed `openvpn` and `easy-rsa`.

`easy-rsa` is a tool that helps create and manage certificates. Think of certificates like digital ID cards — they prove that the machine connecting to the VPN is actually who it claims to be.

```bash
sudo apt-get update && sudo apt-get upgrade
apt update && apt install -y openvpn easy-rsa
```

![apt update running on Kali.](/assets/img/blog/openvpn-kali-linux-mint-project/image3.jpeg)

![apt update running on Linux Mint.](/assets/img/blog/openvpn-kali-linux-mint-project/image4.jpeg)

![OpenVPN and Easy-RSA installation completed.](/assets/img/blog/openvpn-kali-linux-mint-project/image5.jpeg)

---

## Step 2 — Build the PKI on the Server (Kali)

Set up the certificate authority, generated the server cert, DH parameters, and TLS auth key.

```bash
make-cadir ~/openvpn-ca && cd ~/openvpn-ca
./easyrsa init-pki
./easyrsa build-ca nopass
./easyrsa gen-req server nopass
./easyrsa sign-req server server
./easyrsa gen-dh
openvpn --genkey secret ta.key
```

> Note: At prompts for server/client name, just hit Enter. When asked to confirm details, type **yes**.

![PKI initialized and CA built on Kali.](/assets/img/blog/openvpn-kali-linux-mint-project/image6.jpeg)

![Server certificate signed and DH parameters generated.](/assets/img/blog/openvpn-kali-linux-mint-project/image7.jpeg)

![TLS auth key generated.](/assets/img/blog/openvpn-kali-linux-mint-project/image8.jpeg)

---

## Step 3 — Generate Client Certificate

Generated a separate certificate for the client machine. Each device that connects to the VPN needs its own certificate.

```bash
./easyrsa gen-req client1 nopass
./easyrsa sign-req client client1
```

> Note: At prompts, hit Enter for name, type **yes** to confirm.

![client1 certificate request and signing completed.](/assets/img/blog/openvpn-kali-linux-mint-project/image9.jpeg)

---

## Step 4 — Create server.conf on Kali

Created `/etc/openvpn/server.conf` with the server settings. This file tells OpenVPN where to find the certificates, which port to listen on, what IP range to give to VPN clients, and what encryption to use.

```bash
nano /etc/openvpn/server.conf
```

```
port 1194
proto udp
dev tun
ca /root/openvpn-ca/pki/ca.crt
cert /root/openvpn-ca/pki/issued/server.crt
key /root/openvpn-ca/pki/private/server.key
dh /root/openvpn-ca/pki/dh.pem
tls-auth /root/openvpn-ca/ta.key 0
server 10.8.0.0 255.255.255.0
keepalive 10 120
cipher AES-256-CBC
persist-key
persist-tun
status /var/log/openvpn-status.log
verb 3
```

Save and exit with `Ctrl+X`, then `Y`.

Port 1194 UDP is the default OpenVPN port. The `server 10.8.0.0` line means VPN clients will get IP addresses in the 10.8.0.x range — this is a virtual subnet separate from the physical network. AES-256-CBC is the encryption algorithm — it is the same standard used by banks and governments.

![server.conf saved in nano on Kali.](/assets/img/blog/openvpn-kali-linux-mint-project/image10.jpeg)

---

## Step 5 — Enable IP Forwarding & Start OpenVPN Server

IP forwarding allows the server to pass traffic between the VPN tunnel and the regular network. Without this, packets coming in through the VPN have nowhere to go.

```bash
echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
sudo systemctl start openvpn@server
sudo systemctl enable openvpn@server
```

![IP forwarding enabled and OpenVPN server service started.](/assets/img/blog/openvpn-kali-linux-mint-project/image11.jpeg)

---

## Step 6 — Transfer Certificates from Kali to Linux Mint

The client machine needs a copy of the CA cert, its own certificate, its private key, and the `ta.key`. These were served from Kali using Python's built-in HTTP server and downloaded on Linux Mint through the browser.

This is a common quick method for transferring files between two machines on the same network — Python starts a temporary web server in whatever folder you run it from, and the other machine downloads from it like any website. In a real environment you would use SCP or a more secure method.

```bash
cd /tmp
cp /root/openvpn-ca/pki/ca.crt .
cp /root/openvpn-ca/pki/issued/client1.crt .
cp /root/openvpn-ca/pki/private/client1.key .
cp /root/openvpn-ca/ta.key .
python3 -m http.server 8080
```

On Linux Mint, open a browser and go to `http://192.168.147.131:8080` — download all 4 files and save them to `/home/osboxes/`.

![Files staged in /tmp and Python HTTP server running on Kali.](/assets/img/blog/openvpn-kali-linux-mint-project/image12.jpeg)

![Linux Mint browser downloading certificate files from Kali's HTTP server.](/assets/img/blog/openvpn-kali-linux-mint-project/image13.jpeg)

![Certificate files downloaded to Linux Mint.](/assets/img/blog/openvpn-kali-linux-mint-project/image14.jpeg)

---

## Step 7 — Create client.ovpn on Linux Mint

Created the client config file on Linux Mint. This tells OpenVPN on the client side where the server is, which certs to use, and what settings to match the server with.

```bash
nano /home/osboxes/client.ovpn
```

```
client
dev tun
proto udp
remote 192.168.147.131 1194
resolv-retry infinite
nobind
ca ca.crt
cert client1.crt
key client1.key
tls-auth ta.key 1
cipher AES-256-CBC
verb 3
```

The `remote` line points to the Kali server IP and port. The `tls-auth` line uses `1` on the client side (vs `0` on the server) — this is just how OpenVPN distinguishes which end is which for the TLS key.

![client.ovpn file created on Linux Mint.](/assets/img/blog/openvpn-kali-linux-mint-project/image15.jpeg)

![client.ovpn contents verified in terminal.](/assets/img/blog/openvpn-kali-linux-mint-project/image16.jpeg)

---

## Step 8 — Connect & Verify the VPN Tunnel

Ran OpenVPN on Linux Mint with the client config. The tunnel came up and Linux Mint was assigned VPN IP `10.8.0.2` by the server.

```bash
sudo openvpn --config client.ovpn
```

![OpenVPN connecting on Linux Mint — handshake and certificate verification in progress.](/assets/img/blog/openvpn-kali-linux-mint-project/image17.jpeg)

![Tunnel up: VERIFY OK, Peer Connection Initiated, Linux Mint assigned 10.8.0.2, AES-256-GCM active.](/assets/img/blog/openvpn-kali-linux-mint-project/image18.jpeg)

---

## Test — Ping Through the VPN

Pinged Kali's VPN IP (`10.8.0.1`) from Linux Mint to confirm the encrypted tunnel is working in both directions.

When Linux Mint pings `10.8.0.1`, it recognizes that IP belongs to the VPN tunnel and hands the packet to OpenVPN. OpenVPN encrypts it and sends it over the physical network to Kali. Kali decrypts it, responds, and sends an encrypted reply back. Getting replies means the tunnel is up, authentication worked, and encryption is running in both directions.

```bash
ping 10.8.0.1
```

![Successful ping to 10.8.0.1 confirming the VPN tunnel is live and encryption is working.](/assets/img/blog/openvpn-kali-linux-mint-project/image19.jpeg)
