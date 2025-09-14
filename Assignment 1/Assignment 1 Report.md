# Shaikh Islam — Assignment 1 Report
*(Course: CSE 5350 — Quantitative Computer Architecture)*  
*Date: 2025-09-13*

> **Instructions**: Keep this report **≤ 3 pages** including figures/screenshots. Replace placeholders in ALL CAPS.

---

## 1) Device Under Test (DUT)
- **Device**: MAKE MODEL (e.g., 2023 Dell XPS 13 / iPhone 14 / Pixel 7)
- **CPU / SoC**: NAME (cores/threads, base/boost if known)
- **GPU**: NAME (integrated/discrete; VRAM if known)
- **Memory**: SIZE & TYPE (e.g., 16 GB LPDDR5-6400)
- **Storage**: TYPE (e.g., NVMe SSD / SATA SSD / UFS / eMMC) & SIZE
- **OS & Version**: NAME (e.g., Windows 11 24H2 / macOS 15 / Android 15 / iOS 18)
- **Power mode**: PLUGGED-IN or BATTERY; performance/balanced mode if applicable
- **Ambient**: Approx. room temp if known

## 2) Benchmark Tools (2 total)
List each tool with a 1–2 sentence description and link.

- **Tool A**: NAME — WHAT IT MEASURES (e.g., CPU single/multi-core; memory bandwidth/latency). URL
- **Tool B**: NAME — WHAT IT MEASURES (e.g., GPU graphics; storage throughput/IOPS). URL

## 3) Methodology (how each runs)
For each tool, explain **how the run works**:
- Does it run once or multiple iterations? Time-limited or work-limited?
- What workload types (e.g., integer vs FP, compression, FFT, image filters, physics, path tracing, random 4K I/O)?
- Any **test settings** changed from default? Note resolution for graphics tests (onscreen/offscreen), queue depth for storage, etc.

### Tool A — Method
- Version: X.Y.Z  
- Settings: DEFAULTS or LIST CHANGES  
- Runs: NUMBER OF RUNS / DURATION  
- Notes: BACKGROUND APPS CLOSED? THERMALS?

### Tool B — Method
- Version: X.Y.Z  
- Settings: DEFAULTS or LIST CHANGES  
- Runs: NUMBER OF RUNS / DURATION  
- Notes: BACKGROUND APPS CLOSED? THERMALS?

## 4) Results (with screenshots)
Insert screenshots under each subsection. Also put the **raw numbers** in a small table.

### Tool A — Results
| Metric | Score / Value | Units | Notes |
|---|---:|---|---|
| EXAMPLE | 1234 | pts | Single-core |
| EXAMPLE | 5678 | pts | Multi-core |

*(Screenshot A here)*

### Tool B — Results
| Metric | Score / Value | Units | Notes |
|---|---:|---|---|
| EXAMPLE | 2100 | MB/s | Seq Read |
| EXAMPLE | 1900 | MB/s | Seq Write |

*(Screenshot B here)*

## 5) Comparison to Other Systems
Explain what you compared against (same CPU/GPU, similar class, or prior-gen). Cite your sources (tool result browsers, vendor pages, reviews).

| System | Key Specs | Metric | Their Score | Your Score | Δ (%) |
|---|---|---|---:|---:|---:|
| REF SYSTEM | CPU/GPU | e.g., Single-core | 1500 | 1234 | -17.7 |
| REF SYSTEM | Storage | Seq Read | 3500 MB/s | 2100 MB/s | -40.0 |

**Interpretation**: Why are you higher/lower? (power mode, cooling, throttling, storage type, drivers, OS, test version).

## 6) What is “CPU speed” here?
Briefly define: frequency vs IPC, single vs multi-core scaling, memory hierarchy effects, and how the chosen benchmark **infers** speed (e.g., composite workload score normalized to a baseline, or wall-clock time for fixed work). Mention whether your tools also measured **disk I/O**, **graphics**, **memory**, or **flash** and how (throughput MB/s, IOPS, FPS, bandwidth/latency).

## 7) Takeaways
- Key strengths/weaknesses of your DUT  
- Any anomalies and how you validated  
- Practical implications (compile times, gaming, ML, photo/video)

## 8) References
- TOOL A result page (permalink)  
- TOOL B result page (permalink)  
- Any comparison sources

---

### Appendix (optional)
Extra screenshots or thermal/power plots if you have them.
