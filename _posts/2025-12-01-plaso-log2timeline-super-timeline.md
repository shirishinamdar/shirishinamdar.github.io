---
title: "Generating a Forensic Super-Timeline with Plaso and log2timeline"
date: 2025-12-01 18:00:00 -0500
categories: [Digital Forensics, DFIR]
tags: [Plaso, log2timeline, psort, l2tcsv, DFRWS, NIST CFReDS, Super Timeline, Timeline Analysis, Digital Forensics, Project]
description: Building a forensic super-timeline from a disk image with Plaso, running log2timeline against the NIST CFReDS DFRWS 2005 RHINO.dd test image, converting the plaso.dump storage file to l2tcsv with psort, and reviewing the color-coded output that keeps a long timeline navigable.
image:
  path: /assets/img/blog/plaso-log2timeline-dfrws2005/color_timeline_sample.png
  alt: "Sample color-coded l2tcsv rows showing USB, file opening, web history, execution, folder opening, log, deleted data categories."
---

**Plaso** is an open-source Python framework that parses artifacts from a disk image and produces a **super-timeline**: a single, unified, time-ordered list of every event the parsers can extract, from filesystem timestamps and Windows registry hives to browser history, event logs, and shellbags. `log2timeline` is the collector that walks the image; `psort` sorts and exports the collected events into a reviewable format.

This walkthrough runs the toolchain against the **NIST CFReDS DFRWS 2005 RODEO** test image (`RHINO.dd`), a public test set specifically designed for forensic tool exercises, so nothing here touches real evidence.

Source of the image: [cfreds-archive.nist.gov/dfrws/DFRWS2005-RODEO.zip](https://cfreds-archive.nist.gov/dfrws/DFRWS2005-RODEO.zip).

---

## 1 - Download Plaso

Download `plaso-20191203-py3.7-win32.zip` from the Plaso GitHub releases and extract it.

![Plaso release download and extraction folder.](/assets/img/blog/plaso-log2timeline-dfrws2005/image5.png)

---

## 2 - Get the Test Image

Extract the DFRWS 2005 RODEO zip into the same folder as Plaso. Inside is `RHINO.dd`, the raw disk image we'll process.

![DFRWS 2005 RODEO archive extracted alongside the Plaso folder.](/assets/img/blog/plaso-log2timeline-dfrws2005/image2.png)

---

## 3 - Open a Command Prompt in the Plaso Folder

Open Command Prompt and `cd` to the Plaso folder where the binaries and the `RHINO.dd` image are.

![Command Prompt open in the Plaso working folder.](/assets/img/blog/plaso-log2timeline-dfrws2005/image8.png)

---

## 4 - Run log2timeline

```
log2timeline.exe plaso.dump RHINO.dd
```

This scans the disk image and builds a complete forensic timeline of every event the Plaso parsers can extract, saving the result into `plaso.dump`. The `plaso.dump` file is Plaso's own storage format; it isn't human readable on its own, which is what `psort` is for in the next step.

![log2timeline running against RHINO.dd and writing plaso.dump.](/assets/img/blog/plaso-log2timeline-dfrws2005/image6.png)

---

## 5 - Export to CSV with psort

Now convert the `plaso.dump` storage file to a CSV you can actually open:

```
psort.exe -o l2tcsv -w timelinne.csv plaso.dump
```

What each flag does:

- `psort.exe` - processes the Plaso storage file
- `-o l2tcsv` - output format, the standard log2timeline CSV
- `-w timeline.csv` - write to `timeline.csv`
- `plaso.dump` - the storage file created in the previous step

![psort producing the l2tcsv output from plaso.dump.](/assets/img/blog/plaso-log2timeline-dfrws2005/image3.png)

---

## 6 - Timeline Ready in the Plaso Folder

The CSV lands in the Plaso folder alongside `plaso.dump`, ready to open in a spreadsheet.

![Plaso working folder now containing the generated timeline CSV.](/assets/img/blog/plaso-log2timeline-dfrws2005/image1.png)

Because MS Office wasn't installed on the workstation I ran this on, I opened the CSV in Google Docs to review it.

![Generated timeline opened in Google Docs for review.](/assets/img/blog/plaso-log2timeline-dfrws2005/image7.png)

---

## Making a Long Timeline Navigable

Even a small disk image like RHINO produces thousands of rows. Color-coding by event category is a common way to keep the timeline navigable: the eye finds a red **EXECUTION** row or a blue **DEVICE or USB USAGE** row much faster than it scans plain text.

The scheme I use, matching the `TIMELINE_COLOR_TEMPLATE.xlsx` legend:

- Green - **FILE OPENING**
- Amber - **WEB HISTORY**
- Red - **EXECUTION**
- Blue - **DEVICE or USB USAGE**
- Darker green - **FOLDER OPENING**
- Light gray - **LOG FILE**
- Black - **DELETED DATA**

Applied to a compact sample so the visual pattern reads clearly:

![Sample color-coded l2tcsv rows illustrating the category colors.](/assets/img/blog/plaso-log2timeline-dfrws2005/color_timeline_sample.png)

*Sample only, illustrative rows using the same color scheme as the template. Not actual findings from the RHINO image, this is here purely to show what the color coding looks like on real l2tcsv columns.*

---

## Where the Super-Timeline Fits in a Case

The `plaso.dump` output is the raw material. Working from it, an analyst typically:

- Applies the color scheme above to categorize events at a glance
- Filters on a suspicious time window to isolate a session of activity
- Looks for co-occurring events across categories (a USB mount, followed by a file open, followed by a browser upload) that tell a coherent story
- Pivots from an interesting event back into the source artifact (event log, prefetch, shellbag) for confirmation

The value of Plaso is not that it answers the questions on its own, it's that it puts every artifact on the same timeline so the analyst can see the sequence.
