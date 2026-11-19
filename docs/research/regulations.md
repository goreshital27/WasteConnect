# Regulatory Landscape for a Recyclable Waste Marketplace (India & Pune)

**Document Type:** Regulatory Compliance & Statutory Mapping  
**Project:** WasteConnect (Dry Recyclables Marketplace Pilot, Pune)  
**Date of Research / Access:** November 19, 2026  
**Disclaimer:** Prepared strictly for academic and engineering product-scoping purposes. This document does not constitute formal legal counsel.

---

## 1. Core Waste Management & Scrap Trading Regulations

### 1. Solid Waste Management Rules, 2016 (SWM Rules, 2016)
* **Applicable Year / Version:** 2016 (Notified by the Ministry of Environment, Forest and Climate Change - MoEFCC under the Environment (Protection) Act, 1986; in force today).
* **What it says:** Mandates that all waste generators segregate waste at source into three streams—bio-degradable (wet), non-biodegradable (dry), and domestic hazardous. Bulk Waste Generators (BWGs: facilities generating >100 kg/day or gated communities/institutions with an area >5,000 sq. meters) must process bio-degradable waste on-site (composting/bio-methanation) and hand over segregated dry recyclables exclusively to authorized waste pickers, registered recyclers, or urban local bodies.
* **Source URL:** [Central Pollution Control Board - SWM Rules 2016](https://cpcb.nic.in/displaypdf.php?id=c3dtL3N3bS1ydWxlcy0yMDE2LnBkZg==) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** WasteConnect cannot accept unsorted or mixed waste. If onboarding bulk sellers (such as housing societies or IT parks in Pune), the platform must require sellers to certify that materials are segregated dry recyclables and ensure handoffs occur only to verified authorized collectors.

---

### 2. Plastic Waste Management Rules, 2016 (as amended through 2024, including EPR Schedule II)
* **Applicable Year / Version:** 2016, with enforceable amendments in 2021, 2022, 2023, and 2024.
* **What it says:** Prohibits identified single-use plastics and establishes a mandatory Extended Producer Responsibility (EPR) digital regime. Plastic packaging must be classified into four distinct categories (Category I: Rigid, Category II: Flexible/film, Category III: Multi-layered, Category IV: Compostable), and recycling transactions must be reported through the centralized Central Pollution Control Board (CPCB) EPR portal by registered Plastic Waste Processors (PWPs).
* **Source URL:** [CPCB Centralized EPR Portal for Plastic Packaging](https://cpcb.nic.in/epr-plastic-waste/) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** Dry plastic scrap cannot simply be listed as generic "plastic." The MVP should categorize plastic lots by resin type (PET, HDPE, LDPE, PP) and packaging format (rigid vs flexible). This enables downstream aggregators and recyclers to generate compliant audit trails for CPCB EPR certificates, which substantially increases the commercial value of the scrap.

---

### 3. Pune Municipal Corporation (PMC) Solid Waste Management Bye-Laws & Waste Picker Framework
* **Applicable Year / Version:** Approved by PMC General Body in December 2017 (effective from 2018; operating under the Maharashtra Municipal Corporations Act and SWM Rules 2016).
* **What it says:** Mandates 100% source segregation across Pune, authorizes informal waste pickers integrated via the SWaCH cooperative to conduct door-to-door collection with PMC-issued credentials, empowers collectors to levy regulated monthly user fees directly from households, and penalizes non-segregation, open burning, and unauthorized commercial dumping.
* **Source URL:** [Pune Municipal Corporation - Solid Waste Management](https://pmc.gov.in) and [SWaCH Institutional Framework](https://swachcoop.com) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** WasteConnect must not establish an independent door-to-door residential pickup service in Pune that bypasses SWaCH, as doing so conflicts with municipal bye-laws and creates friction with unionized waste workers. The MVP should operate strictly as a B2B trading tool connecting neighborhood waste collectors and local kabadiwalas (who legally own the collected dry scrap) with wholesale scrap aggregators.

---

### 4. Wet / Organic Waste Processing Regulations
* **Applicable Year / Version:** SWM Rules, 2016 (Rules 4 and 11) & Fertilizer (Inorganic, Organic or Mixed) (Control) Order, 1985 (as amended).
* **What it says:** Directs that organic/wet waste be processed on-site via composting or biomethanation by Bulk Waste Generators or handled at decentralized municipal plants without mixing with dry recyclables; any commercial compost produced must adhere to statutory heavy metal and quality standards set forth in Schedule II of the SWM Rules and the Fertilizer Control Order (FCO).
* **Source URL:** [Ministry of Housing and Urban Affairs - SWM Rules](https://sbmurban.org) & [Central Pollution Control Board Guidelines](https://cpcb.nic.in) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** The student project should strictly exclude wet waste trading from the MVP pilot. Wet waste is highly perishable, creates odor and leachate liabilities under municipal health codes if stored in scrap godowns, and trading compost requires laboratory nutrient certification under the Fertilizer Control Order.

---

## 2. Regulatory Exclusion Boundaries (What WasteConnect MUST Exclude)

The following waste streams are governed by dedicated statutory frameworks with stringent handling, storage, and licensing mandates. WasteConnect must explicitly exclude them from the marketplace MVP.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   WASTE STREAMS EXCLUDED FROM MVP                      │
├──────────────────────┬──────────────────────┬──────────────────────────┤
│ Stream               │ Governing Regulation │ Core Exclusion Mandate   │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ E-Waste              │ E-Waste Rules 2022   │ CPCB portal only;        │
│                      │                      │ no uncertified scrap     │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ Lead/Li Batteries    │ Battery Rules 2022   │ Toxic lead/acid hazard;  │
│                      │                      │ strictly CPCB EPR portal │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ Biomedical / Sharps  │ BMW Rules 2016       │ Pathogenic biohazard;    │
│                      │                      │ CBMWTF barcode tracking  │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ Industrial Hazardous │ Hazardous Rules 2016 │ Flammable/toxic residue; │
│                      │                      │ MPCB Form 10 manifests  │
└──────────────────────┴──────────────────────┴──────────────────────────┘
```

### 1. E-Waste (Management) Rules, 2022
* **Applicable Year / Version:** 2022 (G.S.R. 801(E), in force from April 1, 2023, superseding the 2016 rules).
* **What it says:** Regulates all notified Electrical and Electronic Equipment (EEE), mandating that collection, dismantling, and recycling occur exclusively through entities registered on the centralized CPCB e-waste portal under strict Extended Producer Responsibility (EPR) quotas.
* **Source URL:** [MoEFCC Notification - E-Waste (Management) Rules 2022](https://moef.gov.in/wp-content/uploads/2022/11/GSR-801E-E-Waste-Rules-2022.pdf) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** WasteConnect must ban e-waste (appliances, motherboards, circuit boards) on the platform. Facilitating informal scrap transactions of e-waste violates CPCB directives and exposes the platform to environmental liability penalties.

---

### 2. Battery Waste Management Rules, 2022
* **Applicable Year / Version:** 2022 (Notified August 22, 2022, superseding the Batteries (Management and Handling) Rules, 2001).
* **What it says:** Covers all chemistries (lead-acid, lithium-ion, nickel-cadmium) across portable, automotive, and industrial batteries; prohibits battery disposal in landfills and open burning, requiring formal buy-back and recycling via CPCB-registered processors.
* **Source URL:** [MoEFCC Notification - Battery Waste Management Rules 2022](https://moef.gov.in/wp-content/uploads/2022/08/Battery-Waste-Management-Rules-2022.pdf) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** Scrap vehicle, inverter, and mobile batteries must be strictly excluded. Unlicensed storage or trading of batteries risks chemical spills and toxic lead exposure and is legally restricted to certified EPR channels.

---

### 3. Bio-Medical Waste Management Rules, 2016 (as amended)
* **Applicable Year / Version:** 2016 (Notified under Environment (Protection) Act, 1986).
* **What it says:** Mandates that healthcare institutions, pathological laboratories, and clinics segregate clinical waste into four color-coded categories (Yellow, Red, White, Blue) and route all materials exclusively through authorized Common Bio-Medical Waste Treatment Facilities (CBMWTF) with barcoded digital manifests.
* **Source URL:** [Central Pollution Control Board - BMW Rules 2016](https://cpcb.nic.in/bio-medical-waste-rules/) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** WasteConnect must bar all medical equipment, clinical plastics, syringes, expired medicines, and domestic sanitary waste. Handling infectious or contaminated items carries immediate criminal liability and poses severe health hazards to informal waste workers.

---

### 4. Hazardous and Other Wastes (Management and Transboundary Movement) Rules, 2016
* **Applicable Year / Version:** 2016 (Notified by MoEFCC).
* **What it says:** Strictly governs the generation, storage, and transportation of toxic, flammable, reactive, or corrosive industrial materials, requiring formal authorization from State Pollution Control Boards (MPCB in Maharashtra) and physical Form 10 consignment manifests.
* **Source URL:** [Central Pollution Control Board - Hazardous Waste Rules 2016](https://cpcb.nic.in/displaypdf.php?id=aGF6YXJkb3Vzd2FzdGUvSFdfUnVsZXNfMjAxNi5wZGY=) (Accessed: November 19, 2026)
* **What this means for a marketplace MVP (Inference):** The platform must ban empty pesticide containers, industrial chemical barrels, solvent tins, and paint drums unless they are certified as completely decontaminated, as uncleaned containers qualify as hazardous waste under MPCB scrutiny.
