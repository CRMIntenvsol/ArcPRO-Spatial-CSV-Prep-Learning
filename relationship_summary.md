# Summary of Potential Soil-Site Relationships

Based on a comprehensive analysis of the NLP-Markdown repository (9,562 relationship sentences analyzed), the following patterns have emerged connecting soil types, geomorphic settings, and archaeological components.

## 1. Deep Alluvium & Clay = Paleoindian Potential
**Rationale:** Paleoindian sites (e.g., Aubrey, Clovis) are frequently documented as being deeply buried (often 2-8 meters) within Holocene alluvium, specifically in clay or silty clay matrices. These sites are often invisible on the surface.
**Rule:** If `soil_desc` or `geo_setting` mentions "deep alluvium", "Pleistocene terrace", or "clay-rich vertisol" AND depth is significant -> **High Probability of Paleoindian**.

## 2. Sandy Loam Terraces = Archaic & Late Prehistoric Campsites
**Rationale:** A strong correlation exists between "Sandy Loam" soils on river terraces and intensive occupation sites (campsites, middens) from the Archaic and Late Prehistoric periods. These soils offered better drainage and were preferred for habitation over the sticky clays of the floodplain.
**Rule:** If `soil_desc` contains "sandy loam" AND `site_type` is "campsite" or "midden" -> **Likely Archaic or Late Prehistoric**.

## 3. Upland Gravels = Archaic Lithic Scatters
**Rationale:** Upland settings with "Uvalde Gravels" or "lag gravels" are predominantly associated with lithic procurement and reduction stations, often dating to the Archaic period.
**Rule:** If `topo_setting` is "Upland" AND `materials` contains "gravel/chert" -> **Likely Archaic Lithic Scatter**.

## 4. Floodplain Surfaces = Late Prehistoric / Caddo
**Rationale:** Late Prehistoric (including Caddo and Toyah phase) sites are often found in the upper, more recent alluvial deposits (sandy loams/silts) of the active floodplain.
**Rule:** If `topo_setting` is "Floodplain" AND `soil_desc` is "silty loam" or "sand" -> **Likely Late Prehistoric**.

## 5. Soil Texture as a Proxy for Site Function
*   **Clay/Greasy Clay:** Often associated with "burned rock middens" and "ovens" (Class 3 sites) where heat retention was maximized.
*   **Sand/Sandy Loam:** Associated with "hearths" (Class 2 sites) and short-term campsites.

## Proposed Integration into Classification Script
I will update `classify_sites.py` to include a `infer_soil_context(text)` function that scans for these keywords and appends a "Soil-Inferred Context" tag to the classification output. This will help flag sites that lack diagnostic artifacts but have high-potential geomorphic settings.
