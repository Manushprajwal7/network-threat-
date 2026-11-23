# Task 2 Report: Feature Schema and Label Distribution Audit

## 1. Feature Schema Verification
- **Total Features**: 46
- **Canonical Feature List** (in order):
`flow_duration`, `Header_Length`, `Protocol Type`, `Duration`, `Rate`, `Srate`, `Drate`, `fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`, `ack_count`, `syn_count`, `fin_count`, `urg_count`, `rst_count`, `HTTP`, `HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IPv`, `LLC`, `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `IAT`, `Number`, `Magnitue`, `Radius`, `Covariance`, `Variance`, `Weight`

### Verification Findings:
- `Srate` is present at index 5.
- `Drate` is present at index 6.
- `State` is **NOT** present (0 occurrences in raw dataset).
- `Date` is **NOT** present (0 occurrences in raw dataset).
- The erroneous references to "State" and "Date" in previous drafts arose from OCR/autocorrect typos of `Srate` (source packet rate) and `Drate` (destination packet rate).
- Original spelling in dataset retains `Magnitue` at index 41.

## 2. Class and Family Schema
- **Total Classes**: 34
  - Benign Classes: 1 (`BenignTraffic`)
  - Attack Classes: 33
- **Families**: 8 functional groupings:
  - Benign: 1 class (`BenignTraffic`)
  - DDoS: 12 classes
  - DoS: 4 classes
  - Mirai: 3 classes
  - Spoofing: 2 classes
  - Recon: 5 classes
  - Web: 5 classes (`CommandInjection`, `SqlInjection`, `Uploading_Attack`, `XSS`, `BrowserHijacking`)
  - BruteForce: 1 class (`DictionaryBruteForce`)
  - Malware: 1 class (`Backdoor_Malware`)
  *(Note: In Table 9 family aggregation, `Backdoor_Malware` with N=1 test flow is either aggregated under Web or reported as the 8th attack family; documentation clarified).*

## 3. Test Partition Statistics
- Total test flows: 1,176,851
- Benign test flows: 27,709 (2.355%)
- Attack test flows: 1,149,142 (97.645%)
