# Server Label Generator

This Python script automates the generation of server labels using the DCIM API.  
It retrieves the following information for each server:
- **Inventory number**
- **Server name**
- **Server ID**

Based on this data, the script creates:
- A **QR code** containing the inventory number  
- A **QR code** linking directly to the server’s DCIM page  
- The **server name** displayed in the center of the label  

Once all labels are generated, the script automatically sends them to a printer.  
This significantly simplifies inventory checks and ensures accurate identification of servers.

---

## Features
- Automated label generation through DCIM API  
- Dual QR codes for quick access and tracking  
- Server name clearly printed on the label  
- Automatic printing of all generated labels  

---

## Usage
Run the script from your terminal with:

```bash
python script.py
