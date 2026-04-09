# MaterialDNA -- Hackathon Master Plan
**Turning waste variability into manufacturing certainty**

## 🔴 The Vision
Manufacturers want to use recycled plastic but are afraid of batch variability. MaterialDNA is the AI-powered middleware that extracts engineering specs from messy PDFs, creates Digital Product Passports, and connects them directly to factory hardware for auto-tuning.

---

## 🟢 Market Research & The "Gap"

### Current Landscape
1. **Traceability Platforms (DPP):** (e.g., R-Cycle, Circularise). Focus on *provenance* (where it came from).
2. **AI Machine Controllers:** (e.g., Sumitomo SHI Demag). Focus on *real-time tuning* after the plastic is in the machine.

### The MaterialDNA Edge (Our "Moat")
* **The "Manual PDF" Gap:** Existing platforms assume digital data. We use AI-agents to "Nuclear Scan" legacy PDF Certificates of Analysis (CoA).
* **The "Auto-Tune" Bridge:** We connect the **Passport Data** (static) directly to **Machine PLC Settings** (dynamic) *before* the run starts. This enables **Zero-Scrap Batch Switching.**
* **The Engineering Marketplace:** We move from "Commodity Pricing" to "Specification Matching" (Vector Search by MFI, Tensile, etc).

---

## 🛠 Tech Stack (Hackathon Prototype)
* **Intelligence:** Gemini 2.5 Flash (for PDF extraction and reasoning).
* **Backend:** FastAPI (Python).
* **Database:** SQLite + ChromaDB (for Semantic Vector Search).
* **Passport:** QR codes linked to JSON-LD structured data.
* **Frontend:** Premium minimalist dashboard (Vite + Vanilla CSS).

---

## 🏃 Implementation Roadmap (Phases)

### Phase 1: Nuclear Scan (The Extraction Agent)
* **Goal:** Turn a messy PDF CoA into a structured JSON "Material Resumé."
* **Tech:** Python + PyMuPDF + Gemini Vision.
* **Key Fields:** Tensile Strength, Melt Flow Index (MFI), Ash Content, Polymer Type.

### Phase 2: Digital Product Passport (Batch Registry)
* **Goal:** Generate a unique ID and QR code for every physical pallet.
* **Output:** A permanent record of the batch "DNA."

### Phase 3: Semantic Marketplace (The Matchmaker)
* **Goal:** Engineers input engineering requirements; AI finds the matching batches.
* **Tech:** Vector Embeddings (Cosine Similarity search).

### Phase 4: Factory API (The Hardware Bridge)
* **Goal:** An endpoint where a machine pings `/optimize?pallet_id=123`.
* **Output:** A config file with optimized machine settings (Heat, Pressure, Speed).

---

## 🏆 Pitch Winning Strategy: The "Wow" Features
1. **"Zero-Scrap" Demo:** Show the machine settings changing automatically based on the batch DNA.
2. **"Compliance-in-a-Box":** Scan a PDF and instantly generate an EU-compliant Digital Product Passport.
3. **"Pre-flight Feasibility":** Predict material failure before the manufacturer even buys the batch.

---

## 📋 Hackathon Checklist
- [ ] Setup FastAPI server.
- [ ] Implement Gemini extraction script for PDF.
- [ ] Create basic SQLite schema for Material Batches.
- [ ] Build a "Passport Preview" UI.
- [ ] Prototype the "Auto-Tune" API endpoint.
