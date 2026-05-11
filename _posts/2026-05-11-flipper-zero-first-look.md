---
title: First Look at the Flipper Zero
date: 2026-05-11 18:54:00 -0400
categories: [Hardware Security]
tags: [Flipper Zero, Hardware, Pentest, Lab]
description: First hands-on with the Flipper Zero — a portable multi-tool for sub-GHz radio, RFID, NFC, infrared, and GPIO. Initial setup, firmware update, and exploring its core capabilities.
image:
  path: /assets/img/blog/flipper-zero-first-look/image1.png
  alt: First Look at the Flipper Zero
---

# Overview: Hands-on activity with the Flipper Zero

Key milestones included receiving the SD card, installing firmware, and
exploring several built-in features including Infrared (IR) control and
NFC scanning.

# 2\. Hardware & Firmware Setup

## 2.1 SD Card Received & Installed

Upon receiving the SD card, it was formatted and inserted into the
Flipper Zero. The device recognized it immediately and prompted for
firmware installation.

![](/assets/img/blog/flipper-zero-first-look/image1.png)

*Figure 1 - SD card detection on Flipper Zero*

![](/assets/img/blog/flipper-zero-first-look/image2.png)

*Figure 2 - Firmware installation in progress*

## 2.2 Firmware Installation

The latest official firmware was flashed successfully via the qFlipper
desktop application. Post-install, the device rebooted and all modules
were confirmed operational.

![](/assets/img/blog/flipper-zero-first-look/image3.png)

*Figure 3 - Firmware version confirmed after install*

![](/assets/img/blog/flipper-zero-first-look/image4.png)

*Figure 4 - Flipper Zero main menu post-firmware*

![](/assets/img/blog/flipper-zero-first-look/image5.png)

*Figure 5 - File system view on SD card*

![](/assets/img/blog/flipper-zero-first-look/image6.png)

*Figure 6 - Settings and system info screen*

# 3\. Infrared (IR) Feature

The Infrared module on the Flipper Zero offers a powerful set of options
for controlling IR-enabled devices. The following capabilities were
explored this week:

## 3.1 Projector Control

The Flipper Zero was used to successfully control a projector using the
Universal Remote feature. IR signals were sent and the projector
responded to power, input switching, and volume commands.

![](/assets/img/blog/flipper-zero-first-look/image7.jpeg)

*Figure 7 - Flipper Zero sending IR signal to projector*

![](/assets/img/blog/flipper-zero-first-look/image8.jpeg)

*Figure 8 - Projector responding to IR command*

![](/assets/img/blog/flipper-zero-first-look/image9.jpeg)

*Figure 9 - IR remote interface on Projector Screen*

## 3.2 TV Control

The same process was applied to a TV. The Flipper Zero successfully sent
IR commands and the TV responded to all tested functions, including
power toggle, volume, and channel control.

![](/assets/img/blog/flipper-zero-first-look/image10.jpeg)

*Figure 10 - TV control via Flipper Zero IR module*

# 4\. NFC Feature

The Flipper Zero supports reading, saving, and emulating NFC cards. A
test scan was performed as a demonstration; however, the card data was
not saved as this was purely exploratory.

![](/assets/img/blog/flipper-zero-first-look/image11.jpeg)

*Figure 11 - NFC scan in progress*

![](/assets/img/blog/flipper-zero-first-look/image12.jpeg)

*Figure 12 - NFC card details displayed (not saved)*

Note: This NFC scan was performed as an example only. No card data was
retained or saved to the device.
