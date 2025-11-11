# ShredMaster - Secure File Shredder

A powerful, user-friendly desktop application for securely deleting files beyond recovery. ShredMaster overwrites your files multiple times with different patterns before deletion, making data recovery virtually impossible.

![Demo Image](Shreadmaster-demo.png)

## Features

- **Multiple Shredding Algorithms**
  - Simple (1-pass): Quick single overwrite with zeros
  - DoD 5220.22-M (3-pass): US Department of Defense standard
  - Gutmann (35-pass): Maximum security with 35 overwrite passes
  - Custom: Define your own patterns and number of passes

- **Secure Operations**
  - Multi-threaded processing for faster shredding
  - Secure file renaming before deletion
  - Dry run mode to preview operations
  - Real-time progress tracking

## Installation

### Prerequisites

- Python 3.7 or higher
- tkinter (usually included with Python)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/cranbru/Shredmaster.git
cd shredmaster
```

2. Run the application:
```bash
python main.py
```

## Usage

1. **Launch the application**
   ```bash
   python main.py
   ```

2. **Add files to shred**
   - Click "Add" to select individual files
   - Click "Browse Dir" to add all files from a directory
   - Remove unwanted files with "Remove" or "Clear"

3. **Configure shredding options**
   - Select an algorithm (Simple, DoD, Gutmann, or Custom)
   - Enable "Dry Run" to test without actually deleting files
   - Enable "Secure Rename" to randomize filenames before deletion
   - Adjust thread count for performance (1-32 threads)
   - For Custom mode, specify patterns (e.g., "00,FF,RANDOM") and passes

4. **Start shredding**
   - Click "Start Shred" to begin
   - Monitor progress in the progress bar and logs
   - Click "Cancel" to stop the operation

## Shredding Algorithms

### Simple (1-pass)
Overwrites files once with zeros. Fast but less secure.

### DoD 5220.22-M (3-pass)
US Department of Defense standard:
- Pass 1: Zeros (0x00)
- Pass 2: Ones (0xFF)
- Pass 3: Random data

### Gutmann (35-pass)
Maximum security method with 35 different patterns. Extremely thorough but slower.

### Custom
Define your own shredding pattern:
- Specify hex patterns (e.g., "00", "FF") or "RANDOM"
- Set the number of passes
- Example: "00,FF,RANDOM" with 5 passes

## Configuration

Settings are automatically saved to `settings.json` and persist between sessions. You can manually edit this file to set defaults.

Example `settings.json`:
```json
{
    "algorithm": "DoD",
    "dry_run": false,
    "secure_rename": true,
    "threads": 4,
    "custom_pattern": "00,FF,RANDOM",
    "custom_passes": 3,
    "log_file": "",
    "mode": "file"
}
```

## Security Notes

**Important Warnings:**

- **Irreversible**: Shredded files cannot be recovered. Use with caution.
- **SSD Limitations**: Modern SSDs with wear-leveling may not fully overwrite data. For maximum security on SSDs, use full-disk encryption.
- **Backups**: Shredding doesn't affect backups or cloud copies of files.
- **Test First**: Always use "Dry Run" mode first to verify you're shredding the correct files.





