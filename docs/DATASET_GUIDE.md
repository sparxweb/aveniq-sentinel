# NeuralShield AI — Dataset Acquisition Guide
**Document:** `docs/DATASET_GUIDE.md`  

---

## 1. Official Dataset Information

- **Dataset Name:** CIC-IDS2017
- **Provider:** Canadian Institute for Cybersecurity (CIC), University of New Brunswick (UNB)
- **Official URL:** https://www.unb.ca/cic/datasets/ids-2017.html
- **Recommended Archive:** `MachineLearningCSV.zip` (~2.2 GB compressed)

---

## 2. Directory Placement

Extract the CSV files from `MachineLearningCSV.zip` directly into:
```text
data/raw/cic_ids2017/
```

### Expected 8 CSV Files
1. `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv`
2. `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv`
3. `Friday-WorkingHours-Morning.pcap_ISCX.csv`
4. `Monday-WorkingHours.pcap_ISCX.csv`
5. `Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv`
6. `Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv`
7. `Tuesday-WorkingHours.pcap_ISCX.csv`
8. `Wednesday-workingHours.pcap_ISCX.csv`

---

## 3. Verification

Run the dataset inventory discovery module to verify file integrity:
```powershell
python -c "from neuralshield.data.discovery import inspect_dataset_inventory; print(inspect_dataset_inventory())"
```
