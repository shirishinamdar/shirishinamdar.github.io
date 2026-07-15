---
title: "Disk Imaging and Forensic Analysis on MicroFRED with FTK Imager and Autopsy"
date: 2025-09-22 18:00:00 -0500
categories: [Digital Forensics, DFIR]
tags: [Disk Imaging, FTK Imager, Autopsy, MicroFRED, E01, DD, Hash Verification, Ingest Modules, Digital Forensics, Project]
description: End to end forensic workflow on the MicroFRED workstation, creating a bit for bit disk image with FTK Imager, choosing between E01 and DD, verifying integrity with hash checks, then importing the image into Autopsy as a new case for ingest module analysis.
image:
  path: /assets/img/blog/disk-imaging-microfred/image2.jpg
  alt: "Hard disk seated in the blue hot swap tray, ready for the SATA bay on the MicroFRED workstation."
---

Disk imaging is the process of creating an exact, bit for bit copy of a storage device, preserving all data, structure, and metadata for forensic analysis. This walkthrough goes through that pipeline end to end on the **MicroFRED** workstation: image the drive with **FTK Imager**, verify the acquisition with hash checks, then load the image into **Autopsy** as a new case for ingest module analysis.

![Pipeline flowchart, FRED + FTK Imager for imaging, Autopsy for analysis.](/assets/img/blog/disk-imaging-microfred/image1.png)

---

## Imaging a Drive with FTK Imager

FTK Imager is a forensic acquisition tool that creates and verifies disk images in formats like **E01** and **DD**, with data integrity confirmed through hashing.

The hard disk to be imaged is placed into a blue hot swap tray and securely inserted into one of the front facing SATA bays of the MicroFRED workstation.

![Hard disk seated in the blue hot swap tray, ready for the SATA bay on the MicroFRED.](/assets/img/blog/disk-imaging-microfred/image2.jpg)

### Step 1 - Open FTK Imager

Launch **FTK Imager** on the FRED machine. Run it as **Administrator** for full disk access.

### Step 2 - Verify the Drive is Detected

- Click **File > Add Evidence Item**.
- Choose **Physical Drive**.
- Select the newly inserted disk and click **Finish**. You can identify it by size or model, for example Toshiba.

![FTK Imager showing the inserted Toshiba physical drive selected as the evidence item.](/assets/img/blog/disk-imaging-microfred/image3.jpg)

Do **not** check "Read Entire Drive" unless you want it loaded into memory, which is usually unnecessary.

### Step 3 - Create a Forensic Image

- Go to **File > Create Disk Image**.
- Choose **Physical Drive**, click **Next**.
- Select the correct source drive (verify it is the right one), click **Finish**.

### Step 4 - Select Image Type

Choose the image type, one at a time:

- **E01**, EnCase image format. Compressed, supports metadata and embedded hash.
- **Raw (dd)**, uncompressed bit for bit copy.

Click **Next**.

![FTK Imager image type selection screen showing E01 and Raw (dd) options.](/assets/img/blog/disk-imaging-microfred/image4.png)

### Step 5 - Fill in Case Info (Optional)

Enter investigator name, case number, evidence number, and so on. These fields are optional but recommended for documentation. Click **Next**.

### Step 6 - Choose Image Destination

- Click **Add** and choose the destination path (external USB drive, evidence partition, and so on).
- Choose segment size (default is fine), compression (only meaningful for E01), and add MD5 / SHA1 hashes.
- Click **Finish**.

### Step 7 - Start Imaging

Review the summary, click **Start**, and monitor progress in the status window.

![FTK Imager imaging progress window during acquisition.](/assets/img/blog/disk-imaging-microfred/image5.jpg)

![FTK Imager status output as the image is written and hashed.](/assets/img/blog/disk-imaging-microfred/image6.jpg)

### Step 8 - Verify the Image

FTK Imager calculates hashes during and after imaging. Make sure the **Verification hash matches the Acquisition hash**. This is what confirms image integrity. If they don't match, the image is suspect and you start over.

---

## Forensic Analysis with Autopsy

Autopsy is a digital forensics platform that analyzes disk images and extracts evidence: files, internet history, deleted artifacts, and more. Its ingest modules automate a large chunk of the analysis on import.

Once the imaging process is complete, the disk image is imported into Autopsy as a new case for examination.

![Autopsy data source diagram, showing how the disk image is added to a new case.](/assets/img/blog/disk-imaging-microfred/image7.png)

### Open Autopsy

Launch via Start Menu or desktop shortcut.

### Create a New Case

Click **Create New Case**, then enter:

- **Case Name**, for example `Toshiba_Investigation`.
- **Base Directory** where all Autopsy data will be saved.

Click **Next**, then **Finish**.

### Add Data Source

From the Case Dashboard:

- Click **Add Data Source**.
- Choose **Local Disk**.

### Select the Target Drive

From the list, choose the drive corresponding to the inserted Toshiba HDD (by model or size). Click **Next**.

### Configure Ingest Modules

The ingest modules are what actually analyze the disk contents. Pick the modules relevant to the case, click **Next**, then **Finish**.

![Autopsy ingest module selection screen for the imported data source.](/assets/img/blog/disk-imaging-microfred/image8.jpg)

From here, Autopsy works through the disk and surfaces the artifacts each module finds, ready for investigat