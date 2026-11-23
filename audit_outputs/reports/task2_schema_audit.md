# Task 2: Feature Schema and Label Count Audit Report

## 1. Feature Schema Corrections
A definitive inspection of the raw feature header array (`feature_columns.pkl`) confirms:
- **Exact Feature Count**: Exactly 46 network flow features.
- **Rate Features**: `Rate` (Index 5), `Srate` (Index 6), and `Drate` (Index 7) are genuinely present.
- **Erroneous Legacy Names**: `State` and `Date` do **not** exist anywhere in the CICIoT2023 dataset schema. The manuscript Section 3.1 must be updated to replace 'State, Date' with 'Srate, Drate'.

### First 10 Features in Canonical Order

|   feature_index | feature_name    | category               |
|----------------:|:----------------|:-----------------------|
|               1 | flow_duration   | Flow Duration / Rate   |
|               2 | Header_Length   | Protocol / Application |
|               3 | Protocol Type   | Protocol / Application |
|               4 | Duration        | Flow Duration / Rate   |
|               5 | Rate            | Flow Duration / Rate   |
|               6 | Srate           | Flow Duration / Rate   |
|               7 | Drate           | Flow Duration / Rate   |
|               8 | fin_flag_number | Flags / Counts         |
|               9 | syn_flag_number | Flags / Counts         |
|              10 | rst_flag_number | Flags / Counts         |

## 2. Granular Class and Attack Family Accounting
- **Total Classes**: Exactly **34 classes** (33 attack classes + 1 BenignTraffic class).
- Claims that there are '34 attack classes + 1 benign = 35 classes' are factually incorrect.
- **8 Macro Attack Families + Benign**:
| Macro Family   |   Number of Granular Classes |
|:---------------|-----------------------------:|
| Benign         |                            1 |
| BruteForce     |                            1 |
| DDoS           |                           12 |
| DoS            |                            4 |
| Malware        |                            1 |
| Mirai          |                            3 |
| Recon          |                            5 |
| Spoofing       |                            2 |
| Web            |                            5 |

## 3. Label Support Summary Across Dataset Partitions

|   class_index | class_name              | macro_family   |   train_support |   val_support |   test_support |
|--------------:|:------------------------|:---------------|----------------:|--------------:|---------------:|
|             0 | Backdoor_Malware        | Malware        |             392 |            93 |             89 |
|             1 | BenignTraffic           | Benign         |          129538 |         27519 |          27709 |
|             2 | BrowserHijacking        | Web            |             665 |           158 |            134 |
|             3 | CommandInjection        | Web            |             620 |           132 |            119 |
|             4 | DDoS-ACK_Fragmentation  | DDoS           |           33581 |          7194 |           7292 |
|             5 | DDoS-HTTP_Flood         | DDoS           |            3371 |           706 |            709 |
|             6 | DDoS-ICMP_Flood         | DDoS           |          848088 |        182011 |         180447 |
|             7 | DDoS-ICMP_Fragmentation | DDoS           |           53046 |         11430 |          11402 |
|             8 | DDoS-PSHACK_Flood       | DDoS           |          481254 |        102985 |         103326 |
|             9 | DDoS-RSTFINFlood        | DDoS           |          475441 |        101563 |         101819 |
|            10 | DDoS-SYN_Flood          | DDoS           |          478653 |        102644 |         102208 |
|            11 | DDoS-SlowLoris          | DDoS           |            2757 |           620 |            622 |
|            12 | DDoS-SynonymousIP_Flood | DDoS           |          422083 |         90795 |          90480 |
|            13 | DDoS-TCP_Flood          | DDoS           |          528499 |        113888 |         113735 |
|            14 | DDoS-UDP_Flood          | DDoS           |          637558 |        136466 |         136717 |
|            15 | DDoS-UDP_Fragmentation  | DDoS           |           34169 |          7221 |           7224 |
|            16 | DNS_Spoofing            | Spoofing       |           21214 |          4565 |           4570 |
|            17 | DictionaryBruteForce    | BruteForce     |            1541 |           290 |            319 |
|            18 | DoS-HTTP_Flood          | DoS            |            8487 |          1833 |           1805 |
|            19 | DoS-SYN_Flood           | DoS            |          237573 |         51115 |          51116 |
|            20 | DoS-TCP_Flood           | DoS            |          314174 |         67056 |          67697 |
|            21 | DoS-UDP_Flood           | DoS            |          390422 |         83446 |          83627 |
|            22 | MITM-ArpSpoofing        | Spoofing       |           36316 |          7741 |           7840 |
|            23 | Mirai-greeth_flood      | Mirai          |          116133 |         24910 |          24934 |
|            24 | Mirai-greip_flood       | Mirai          |           88821 |         18867 |          19279 |
|            25 | Mirai-udpplain          | Mirai          |          104814 |         22314 |          22536 |
|            26 | Recon-HostDiscovery     | Recon          |           15737 |          3482 |           3331 |
|            27 | Recon-OSScan            | Recon          |           11587 |          2500 |           2433 |
|            28 | Recon-PingSweep         | Recon          |             249 |            45 |             53 |
|            29 | Recon-PortScan          | Recon          |            9648 |          2083 |           2082 |
|            30 | SqlInjection            | Web            |             590 |           148 |            148 |
|            31 | Uploading_Attack        | Web            |             140 |            35 |             33 |
|            32 | VulnerabilityScan       | Recon          |            4396 |           905 |            913 |
|            33 | XSS                     | Web            |             414 |            91 |            103 |