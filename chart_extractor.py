import io
import math
import os
import re
import requests
import mido
from Crypto.Cipher import AES

# Master 256-bit AES encryption key for Fortnite Festival MIDI files
FESTIVAL_MIDI_KEY = bytes.fromhex("29B4AC18D090166559244E15548BD4C11B98D33AD57F7B0D9BFFF6CEB7CF6145")


def decrypt_midi(dat_bytes: bytes, key: bytes = FESTIVAL_MIDI_KEY) -> bytes:
    """Decrypt a Fortnite Festival .dat file to standard MIDI bytes (MThd) using AES-256-ECB."""
    if dat_bytes.startswith(b"MThd"):
        return dat_bytes
    if len(dat_bytes) == 0:
        raise ValueError("Cannot decrypt empty data")

    cipher = AES.new(key, AES.MODE_ECB)
    blocks = []
    for i in range(0, len(dat_bytes), 16):
        chunk = dat_bytes[i:i + 16]
        if len(chunk) < 16:
            chunk = chunk + b"\x00" * (16 - len(chunk))
        blocks.append(cipher.decrypt(chunk))
    decrypted = b"".join(blocks)
    if not decrypted.startswith(b"MThd"):
        raise ValueError("Decrypted data does not contain a valid MIDI header (MThd)")
    return decrypted


def midi_to_chart(mid: mido.MidiFile, song_info: dict) -> str:
    """Convert a multi-track decrypted Fortnite Festival MIDI file into a Moonscraper / Clone Hero .chart string."""
    ppqn = mid.ticks_per_beat
    lines = []

    title = song_info.get("title", "Unknown Title")
    artist = song_info.get("artist", "Unknown Artist")
    album = song_info.get("album", "")
    year = song_info.get("release_year", "")
    genre = song_info.get("genre", "")
    if isinstance(genre, list) and genre:
        genre = genre[0]
    duration = song_info.get("duration", 0)

    # Preview start time in seconds
    preview_start = 0
    qi = song_info.get("qi_data", {})
    if isinstance(qi, dict):
        preview = qi.get("preview", {})
        if isinstance(preview, dict):
            preview_start = preview.get("starttime", 0)

    # 1. [Song]
    lines.append("[Song]")
    lines.append("{")
    lines.append(f'  Name = "{title}"')
    lines.append(f'  Artist = "{artist}"')
    lines.append('  Charter = "Harmonix, Epic Games"')
    if album:
        lines.append(f'  Album = "{album}"')
    if year and str(year) != "Unknown Year":
        lines.append(f'  Year = ", {year}"')
    lines.append("  Offset = 0")
    lines.append(f"  Resolution = {ppqn}")
    lines.append("  Player2 = bass")
    lines.append("  Difficulty = 0")
    if preview_start:
        lines.append(f"  PreviewStart = {int(preview_start)}")
        lines.append(f"  PreviewEnd = {int(preview_start) + 30}")
    if genre:
        lines.append(f'  Genre = "{genre}"')
    lines.append('  MediaType = "cd"')
    lines.append('  MusicStream = "song.ogg"')
    lines.append("}")

    # 2. [SyncTrack]
    sync_events = {}
    abs_tick = 0
    tempo_track = mid.tracks[0] if mid.tracks else []
    for msg in tempo_track:
        abs_tick += msg.time
        if msg.type == "time_signature":
            num = msg.numerator
            den = msg.denominator
            if den == 4:
                sync_events.setdefault(abs_tick, []).append(f"TS {num}")
            else:
                exp = int(math.log2(den)) if den > 0 else 2
                sync_events.setdefault(abs_tick, []).append(f"TS {num} {exp}")
        elif msg.type == "set_tempo":
            bpm = mido.tempo2bpm(msg.tempo)
            sync_events.setdefault(abs_tick, []).append(f"B {int(round(bpm * 1000))}")

    lines.append("[SyncTrack]")
    lines.append("{")
    if 0 not in sync_events:
        lines.append("  0 = TS 4")
        lines.append("  0 = B 120000")
    for tick in sorted(sync_events.keys()):
        for ev in sync_events[tick]:
            lines.append(f"  {tick} = {ev}")
    lines.append("}")

    # 3. [Events]
    events_map = {}
    for tr in mid.tracks:
        if tr.name in ("SECTION", "EVENTS", "PRO VOCALS", "PART VOCALS"):
            abs_tick = 0
            for msg in tr:
                abs_tick += msg.time
                if msg.type == "text":
                    raw = msg.text.strip("[]")
                    if tr.name == "SECTION":
                        formatted = raw.replace("_", " ").title()
                        events_map.setdefault(abs_tick, []).append(f'E "section {formatted}"')
                    elif tr.name == "EVENTS":
                        events_map.setdefault(abs_tick, []).append(f'E "{raw}"')
                elif msg.type == "lyrics":
                    lyric = msg.text.strip()
                    if lyric:
                        events_map.setdefault(abs_tick, []).append(f'E "lyric {lyric}"')

    lines.append("[Events]")
    lines.append("{")
    for tick in sorted(events_map.keys()):
        for ev in events_map[tick]:
            lines.append(f"  {tick} = {ev}")
    lines.append("}")

    # 4. Instrument Tracks
    inst_configs = [
        ("Single", ["PLASTIC GUITAR", "PART GUITAR"]),
        ("DoubleBass", ["PLASTIC BASS", "PART BASS"]),
        ("Drums", ["PLASTIC DRUMS", "PART DRUMS"]),
    ]

    diff_offsets = [
        ("Expert", 96),
        ("Hard", 84),
        ("Medium", 72),
        ("Easy", 60),
    ]

    for chart_inst, track_names in inst_configs:
        target_track = None
        for tname in track_names:
            target_track = next((t for t in mid.tracks if t.name == tname), None)
            if target_track:
                break
        if not target_track:
            continue

        is_drums = (chart_inst == "Drums")

        notes_by_pitch = {}
        finished_notes = []
        active_sp = None
        sp_phrases = []
        cymbal_active = {110: None, 111: None, 112: None}
        cymbals = []

        abs_tick = 0
        for msg in target_track:
            abs_tick += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                if msg.note == 116:
                    active_sp = abs_tick
                elif msg.note in (110, 111, 112):
                    cymbal_active[msg.note] = abs_tick
                else:
                    notes_by_pitch[msg.note] = abs_tick
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                if msg.note == 116 and active_sp is not None:
                    sp_phrases.append((active_sp, abs_tick - active_sp))
                    active_sp = None
                elif msg.note in (110, 111, 112) and cymbal_active[msg.note] is not None:
                    cymbals.append((msg.note, cymbal_active[msg.note], abs_tick))
                    cymbal_active[msg.note] = None
                elif msg.note in notes_by_pitch:
                    start_tick = notes_by_pitch.pop(msg.note)
                    finished_notes.append((msg.note, start_tick, abs_tick - start_tick))

        for diff_name, base_pitch in diff_offsets:
            sec_name = f"[{diff_name}{chart_inst}]"
            diff_events = {}

            # Star Power
            for sp_start, sp_len in sp_phrases:
                diff_events.setdefault(sp_start, []).append(f"S 2 {sp_len}")

            # Notes
            for pitch, start_tick, note_duration in finished_notes:
                lane = pitch - base_pitch
                if 0 <= lane <= 4:
                    diff_events.setdefault(start_tick, []).append(f"N {lane} {note_duration}")
                    # Pro Drums Cymbal markers
                    if is_drums and lane in (2, 3, 4):
                        cym_pitch = 110 + (lane - 2)
                        for c_p, c_s, c_e in cymbals:
                            if c_p == cym_pitch and c_s <= start_tick <= c_e:
                                cym_flag = 64 + lane
                                diff_events.setdefault(start_tick, []).append(f"N {cym_flag} 0")
                                break
                elif is_drums and (pitch == 95 or pitch == base_pitch - 1):
                    # Double kick
                    diff_events.setdefault(start_tick, []).append("N 32 0")
                elif not is_drums:
                    if pitch == base_pitch + 5:
                        diff_events.setdefault(start_tick, []).append("N 5 0")  # Force HOPO On
                    elif pitch == base_pitch + 6:
                        diff_events.setdefault(start_tick, []).append("N 6 0")  # Force Strum / HOPO Off

            if diff_events:
                lines.append(sec_name)
                lines.append("{")
                for tick in sorted(diff_events.keys()):
                    for ev in diff_events[tick]:
                        lines.append(f"  {tick} = {ev}")
                lines.append("}")

    return "\n".join(lines)


def create_song_ini(song_info: dict) -> str:
    """Generate a standard Clone Hero / YARG song.ini configuration file."""
    title = song_info.get("title", "Unknown Title")
    artist = song_info.get("artist", "Unknown Artist")
    album = song_info.get("album", "")
    genre = song_info.get("genre", "")
    if isinstance(genre, list) and genre:
        genre = genre[0]
    year = song_info.get("release_year", "")
    if str(year) == "Unknown Year":
        year = ""

    duration = song_info.get("duration", 0)
    try:
        duration_ms = int(duration) * 1000
    except (ValueError, TypeError):
        duration_ms = 0

    preview_ms = 0
    qi = song_info.get("qi_data", {})
    if isinstance(qi, dict):
        preview = qi.get("preview", {})
        if isinstance(preview, dict):
            preview_sec = preview.get("starttime", 0)
            preview_ms = int(float(preview_sec) * 1000)

    intensities = song_info.get("intensities", {})
    if not isinstance(intensities, dict):
        intensities = {}

    diff_guitar = intensities.get("pg", intensities.get("gr", -1))
    diff_bass = intensities.get("pb", intensities.get("ba", -1))
    diff_drums = intensities.get("pd", intensities.get("ds", -1))
    diff_vocals = intensities.get("vl", -1)

    lines = [
        "[song]",
        f"name = {title}",
        f"artist = {artist}",
    ]
    if album:
        lines.append(f"album = {album}")
    if genre:
        lines.append(f"genre = {genre}")
    if year:
        lines.append(f"year = {year}")
    lines.append("charter = Harmonix, Epic Games")
    lines.append("diff_band = -1")
    lines.append(f"diff_guitar = {diff_guitar}")
    lines.append(f"diff_bass = {diff_bass}")
    lines.append(f"diff_drums = {diff_drums}")
    lines.append(f"diff_drums_real = {diff_drums}")
    lines.append(f"diff_vocals = {diff_vocals}")
    lines.append("diff_keys = -1")
    lines.append("diff_guitarghl = -1")
    lines.append("diff_bassghl = -1")
    lines.append(f"preview_start_time = {preview_ms}")
    lines.append("icon = festival")
    if duration_ms > 0:
        lines.append(f"song_length = {duration_ms}")

    return "\n".join(lines) + "\n"


def extract_chart_files(song: dict, target_folder: str, export_chart: bool = True,
                        export_mid: bool = True, export_ini: bool = True,
                        export_album_art: bool = True, session: requests.Session = None) -> list:
    """Download the encrypted .dat file from song['mu'], decrypt to MIDI, generate .chart and song.ini,

    and optionally save album art cover. Returns list of created file paths.
    """
    mu_url = song.get("mu", "")
    if not mu_url:
        print(f"No MIDI URL available for {song.get('title', 'song')}")
        return []

    client = session or requests
    os.makedirs(target_folder, exist_ok=True)
    created_files = []

    print(f"Downloading chart MIDI data from {mu_url}...")
    resp = client.get(mu_url, timeout=30)
    resp.raise_for_status()
    dat_bytes = resp.content

    print(f"Decrypting {len(dat_bytes)} bytes using Festival AES key...")
    midi_bytes = decrypt_midi(dat_bytes)

    # 1. Save notes.mid
    if export_mid:
        mid_path = os.path.join(target_folder, "notes.mid")
        with open(mid_path, "wb") as f:
            f.write(midi_bytes)
        created_files.append(mid_path)
        print(f"Saved: {mid_path}")

    # Parse with mido for .chart conversion
    mid = mido.MidiFile(file=io.BytesIO(midi_bytes))

    # 2. Save notes.chart
    if export_chart:
        chart_content = midi_to_chart(mid, song)
        chart_path = os.path.join(target_folder, "notes.chart")
        with open(chart_path, "w", encoding="utf-8") as f:
            f.write(chart_content)
        created_files.append(chart_path)
        print(f"Saved: {chart_path}")

    # 3. Save song.ini
    if export_ini:
        ini_content = create_song_ini(song)
        ini_path = os.path.join(target_folder, "song.ini")
        with open(ini_path, "w", encoding="utf-8") as f:
            f.write(ini_content)
        created_files.append(ini_path)
        print(f"Saved: {ini_path}")

    # 4. Save album art as album.png
    cover_url = song.get("cover_art_url", "")
    if export_album_art and cover_url:
        album_path = os.path.join(target_folder, "album.png")
        if not os.path.exists(album_path):
            try:
                cover_resp = client.get(cover_url, timeout=15)
                if cover_resp.status_code == 200:
                    with open(album_path, "wb") as f:
                        f.write(cover_resp.content)
                    created_files.append(album_path)
                    print(f"Saved: {album_path}")
            except Exception as e:
                print(f"Could not download album art: {e}")

    return created_files
