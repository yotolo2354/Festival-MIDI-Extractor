# 🎵 Festival MIDI Extractor

![Festival MIDI Extractor](https://i.ibb.co/BvQtR3j/logo2.png)

An advanced GUI tool to download and extract **Fortnite Festival** music tracks into high-quality **audio stems** and **multi-track MIDI notes** (`notes.mid`), directly compatible with **Clone Hero** and **YARG**.

> ℹ️ **Notice of Fork & Credits:**  
> This project is an open-source fork of **[Festival-Extractor](https://github.com/ilayezra/Festival-Extractor)** by **[Ilay Ezra (ilayezra)](https://github.com/ilayezra)**.  
> It extends the original extractor with:
> - Decryption and extraction of official Harmonix multi-track MIDI files (`notes.mid`).
> - Generation of `song.ini` (track difficulty ratings, year, charter, genre, preview start time).
> - Unified song folder structure (all stems, MIDI, `song.ini`, and `album.png` in the exact same directory, ready to drag & drop into Clone Hero / YARG).
> - **1-Click Full Export** button to download all stems and MIDI components in one go.

## 🚀 Features
✅ **Download Fortnite Festival songs** directly using their track IDs  
✅ **Extract audio stems** (Drums, Bass, Lead, Vocals, Other) in multiple formats (`wav`, `mp3`, `flac`)  
✅ **Extract Multi-track MIDI files** – Export `notes.mid` (decrypted official Harmonix multi-track MIDI), `song.ini` (song metadata & difficulty ratings), and `album.png`  
✅ **1-Click Full Export** – Download all stems, MIDI, and metadata together in one unified folder  
✅ **Quick MIDI Export** – Download only the `notes.mid`, `song.ini`, and album art in seconds without needing to download large audio files  
✅ **User-friendly GUI** with dark/light Sun Valley theme    
✅ **Search & Sort** tracks by name, artist, or last added  
✅ **Customizable settings**, including extraction folder, audio format, and naming options  

## 📸 Screenshot
![Festival MIDI Extractor](https://us-east-1.tixte.net/uploads/milki.tixte.co/promo.png)

## 🔧 Installation

Download the file for your system from the latest **[Release](https://github.com/yotolo18804/Festival-Midi-Extractor/releases)** and unzip it.
Everything the program needs is built in - no ffmpeg or other files to install.

### Windows
Run `Festival Extractor.exe` (`FestivalExtractor-Windows-x64.zip`).

### macOS
Use `FestivalExtractor-macOS-AppleSilicon.zip` for M1/M2/M3/M4 Macs or `FestivalExtractor-macOS-Intel.zip` for Intel Macs.
The app isn't signed by Apple, so the first time **right-click `Festival Extractor` → Open → Open**.
If macOS says the app is damaged, run `xattr -cr "/path/to/Festival Extractor.app"` in Terminal once.

### Linux
Unzip `FestivalExtractor-Linux-x64.zip` and run `./"Festival Extractor"`.

### Build from source
```
pip install -r requirements.txt pyinstaller
pyinstaller FFR.spec
```
The program is written to `dist/`. To run without building: `python FFR.py`.

## 🎛 Usage
1. Launch **Festival MIDI Extractor**
2. Search for a song or browse the list
3. Click on a track to view details
4. Press **⚡ Full Export (Stems + MIDI)** to start the extraction
5. Audio stems, `notes.mid`, `song.ini`, and `album.png` will all be saved together in the exact same song folder (ready to drag & drop into Clone Hero / YARG)

## ⚙️ Settings
- **Sorting Options**: Sort tracks by name, artist, or last added  
- **Custom Naming**: Choose if you want more details in your file names  
- **Audio Format**: Export files as `wav`, `mp3`, or `flac`  
- **Extraction Mode**:  
  - **Stereo** (default) – Keeps left & right channels together  
  - **Mono** – Extracts individual channels separately  
  - **Single File** – Merges all channels into one master file  
- **MIDI & Metadata (Clone Hero / YARG)**:  
  - **.mid export**: Decrypts the raw multi-track MIDI file (`notes.mid`)  
  - **song.ini**: Automatically populates track difficulty stars, year, genre, and charter tags  
  - **album.png**: Saves 512x512 high-resolution cover art  

## ©️ Credits
- **[Ilay Ezra (ilayezra)](https://github.com/ilayezra)** – Creator of the original **[Festival-Extractor](https://github.com/ilayezra/Festival-Extractor)**, the GUI application, audio downloading, stem separation, and interface design.
- **[spiritascend](https://github.com/spiritascend)** – Creator of **[blurlconvert](https://github.com/spiritascend/blurlconvert/tree/main)**, whose algorithm enables BLURL stream downloading and parsing.
- **[Harmonix Music Systems & Epic Games](https://www.epicgames.com/)** – Creators of Fortnite Festival, Rock Band, and the underlying multi-track audio & MIDI charts.

## 📜 License
This project is **open-source** and licensed under the **MIT License**, consistent with the upstream project.

## 🤝 Contributing
Feel free to **fork this project** and submit a pull request if you have improvements!

## 📧 Repository & Issues
- **Fork Repository:** [yotolo18804/Festival-Midi-Extractor](https://github.com/yotolo18804/Festival-Midi-Extractor)
- **Original Upstream:** [ilayezra/Festival-Extractor](https://github.com/ilayezra/Festival-Extractor)
- For bug reports or feature requests, open an **[Issue](https://github.com/yotolo18804/Festival-Midi-Extractor/issues)**.
