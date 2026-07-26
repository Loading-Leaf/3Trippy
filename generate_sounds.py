import os
import math
import struct
import wave
import random

SAMPLE_RATE = 44100

def write_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Write mono 16-bit PCM WAV file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        raw_data = bytearray()
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample))
            val = int(clamped * 32767)
            raw_data.extend(struct.pack('<h', val))
        f.writeframes(raw_data)
    print(f"Generated {filename}")

def note_freq(note_str):
    """Convert note name like 'C4', 'F#4', 'Bb4', 'G3' to frequency in Hz."""
    if note_str == 'REST':
        return 0.0
    flats = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = int(note_str[-1])
    key_name = note_str[:-1]
    if key_name in flats:
        key_name = flats[key_name]
    idx = notes.index(key_name)
    n = idx + (octave - 4) * 12 - 9
    return 440.0 * (2.0 ** (n / 12.0))


def generate_sine(freq, duration, vol=0.5):
    num_samples = int(SAMPLE_RATE * duration)
    if freq <= 0:
        return [0.0] * num_samples
    return [vol * math.sin(2 * math.pi * freq * i / SAMPLE_RATE) for i in range(num_samples)]

def generate_square(freq, duration, vol=0.3, duty=0.5):
    num_samples = int(SAMPLE_RATE * duration)
    if freq <= 0:
        return [0.0] * num_samples
    res = []
    for i in range(num_samples):
        t = (i * freq / SAMPLE_RATE) % 1.0
        val = vol if t < duty else -vol
        res.append(val)
    return res

def generate_triangle(freq, duration, vol=0.4):
    num_samples = int(SAMPLE_RATE * duration)
    if freq <= 0:
        return [0.0] * num_samples
    res = []
    for i in range(num_samples):
        t = (i * freq / SAMPLE_RATE) % 1.0
        val = vol * (4.0 * abs(t - 0.5) - 1.0)
        res.append(val)
    return res

def generate_sawtooth(freq, duration, vol=0.3):
    num_samples = int(SAMPLE_RATE * duration)
    if freq <= 0:
        return [0.0] * num_samples
    res = []
    for i in range(num_samples):
        t = (i * freq / SAMPLE_RATE) % 1.0
        val = vol * (2.0 * t - 1.0)
        res.append(val)
    return res

def generate_noise(duration, vol=0.2):
    num_samples = int(SAMPLE_RATE * duration)
    # Random white noise
    random.seed(42 + int(duration * 1000))
    return [vol * (random.random() * 2.0 - 1.0) for _ in range(num_samples)]

def apply_envelope(samples, attack=0.01, decay=0.05, sustain=0.7, release=0.05):
    total = len(samples)
    att_s = int(attack * SAMPLE_RATE)
    dec_s = int(decay * SAMPLE_RATE)
    rel_s = int(release * SAMPLE_RATE)
    
    out = []
    for i in range(total):
        if i < att_s:
            env = i / float(att_s) if att_s > 0 else 1.0
        elif i < att_s + dec_s:
            progress = (i - att_s) / float(dec_s) if dec_s > 0 else 1.0
            env = 1.0 - (1.0 - sustain) * progress
        elif i < total - rel_s:
            env = sustain
        else:
            progress = (total - i) / float(rel_s) if rel_s > 0 else 0.0
            env = sustain * progress
        out.append(samples[i] * env)
    return out

# --- SFX Generators ---

def make_sfx_click():
    dur = 0.04
    samples = generate_square(800, dur, vol=0.2)
    return apply_envelope(samples, attack=0.002, decay=0.01, sustain=0.2, release=0.01)

def make_sfx_select():
    dur = 0.06
    samples = generate_sine(587.33, dur, vol=0.3)
    return apply_envelope(samples, attack=0.005, decay=0.02, sustain=0.4, release=0.01)

def make_sfx_swap():
    dur = 0.12
    num_samples = int(SAMPLE_RATE * dur)
    samples = []
    for i in range(num_samples):
        progress = i / float(num_samples)
        freq = 300 + progress * 400
        val = 0.25 * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
        samples.append(val)
    return apply_envelope(samples, attack=0.01, decay=0.04, sustain=0.5, release=0.03)

def make_sfx_match():
    dur_note = 0.06
    notes = ['C5', 'E5', 'G5']
    samples = []
    for note in notes:
        freq = note_freq(note)
        s = generate_triangle(freq, dur_note, vol=0.35)
        s = apply_envelope(s, attack=0.005, decay=0.02, sustain=0.5, release=0.01)
        samples.extend(s)
    return samples

def make_sfx_combo():
    notes = ['C5', 'E5', 'G5', 'C6']
    dur_note = 0.07
    samples = []
    for note in notes:
        freq = note_freq(note)
        s = generate_square(freq, dur_note, vol=0.25, duty=0.25)
        s = apply_envelope(s, attack=0.005, decay=0.02, sustain=0.6, release=0.02)
        samples.extend(s)
    return samples

def make_sfx_levelup():
    notes = [('G4', 0.1), ('C5', 0.1), ('E5', 0.1), ('G5', 0.15), ('C6', 0.35)]
    samples = []
    for note, dur in notes:
        freq = note_freq(note)
        s = generate_sine(freq, dur, vol=0.4)
        s = apply_envelope(s, attack=0.01, decay=0.04, sustain=0.7, release=0.05)
        samples.extend(s)
    return samples

def make_sfx_gameover():
    notes = [('G4', 0.15), ('E4', 0.15), ('C4', 0.15), ('G3', 0.4)]
    samples = []
    for note, dur in notes:
        freq = note_freq(note)
        s = generate_triangle(freq, dur, vol=0.35)
        s = apply_envelope(s, attack=0.01, decay=0.05, sustain=0.5, release=0.05)
        samples.extend(s)
    return samples

# --- Modern Pop Drum & Instrument Synthesizers ---

def synth_kick(dur=0.15, vol=0.5):
    """Modern punchy sub-kick drum with exponential frequency sweep."""
    num_samples = int(SAMPLE_RATE * dur)
    samples = []
    for i in range(num_samples):
        t = i / float(SAMPLE_RATE)
        freq = 160.0 * math.exp(-30.0 * t) + 35.0
        env = math.exp(-15.0 * t)
        val = vol * env * math.sin(2 * math.pi * freq * t)
        samples.append(val)
    return samples

def synth_snare(dur=0.15, vol=0.4):
    """Crisp pop snare drum with noise pop and tonal body."""
    num_samples = int(SAMPLE_RATE * dur)
    samples = []
    random.seed(int(dur * 500))
    for i in range(num_samples):
        t = i / float(SAMPLE_RATE)
        noise = (random.random() * 2.0 - 1.0) * math.exp(-22.0 * t)
        tone = math.sin(2 * math.pi * 180.0 * t) * math.exp(-35.0 * t)
        val = vol * (0.65 * noise + 0.35 * tone)
        samples.append(val)
    return samples

def synth_hihat_closed(dur=0.05, vol=0.25):
    """Crisp bright closed hi-hat."""
    num_samples = int(SAMPLE_RATE * dur)
    samples = []
    random.seed(int(dur * 1234))
    for i in range(num_samples):
        t = i / float(SAMPLE_RATE)
        noise = (random.random() * 2.0 - 1.0)
        # High pass simulation via alternating sign
        hp = noise * (1 if i % 2 == 0 else -1)
        env = math.exp(-70.0 * t)
        samples.append(vol * hp * env)
    return samples

def synth_hihat_open(dur=0.15, vol=0.25):
    """Sizzling open hi-hat."""
    num_samples = int(SAMPLE_RATE * dur)
    samples = []
    random.seed(int(dur * 4321))
    for i in range(num_samples):
        t = i / float(SAMPLE_RATE)
        noise = (random.random() * 2.0 - 1.0)
        hp = noise * (1 if i % 2 == 0 else -1)
        env = math.exp(-20.0 * t)
        samples.append(vol * hp * env)
    return samples

def synth_pop_bass_note(note_str, duration, vol=0.35):
    """Funky punchy pop synth bass note (triangle + square sub)."""
    if note_str == 'REST':
        return [0.0] * int(SAMPLE_RATE * duration)
    freq = note_freq(note_str)
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / float(SAMPLE_RATE)
        tri = math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)
        sq = 1.0 if (t * freq) % 1.0 < 0.4 else -1.0
        env = math.exp(-4.0 * t)
        val = vol * env * (0.7 * tri + 0.3 * sq)
        samples.append(val)
    return samples

def synth_pop_chord_stab(chord_notes, duration, vol=0.22):
    """Modern pop synth chord stab with bright pluck attack."""
    num_samples = int(SAMPLE_RATE * duration)
    if not chord_notes or chord_notes[0] == 'REST':
        return [0.0] * num_samples
    
    mixed = [0.0] * num_samples
    for note in chord_notes:
        freq = note_freq(note)
        s = generate_triangle(freq, duration, vol=vol)
        # Add soft sine harmonic for warmth
        s2 = generate_sine(freq * 2, duration, vol=vol * 0.4)
        env_s = apply_envelope([s[i] + s2[i] for i in range(len(s))], attack=0.005, decay=0.08, sustain=0.4, release=0.04)
        for i in range(min(num_samples, len(env_s))):
            mixed[i] += env_s[i]
    return mixed

def synth_pop_lead_note(note_str, duration, vol=0.28):
    """Catchy modern synth lead with gentle vibrato and bright pulse width."""
    if note_str == 'REST':
        return [0.0] * int(SAMPLE_RATE * duration)
    freq = note_freq(note_str)
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / float(SAMPLE_RATE)
        vibrato = 1.0 + 0.008 * math.sin(2 * math.pi * 6.0 * t)
        curr_freq = freq * vibrato
        pulse = 1.0 if (t * curr_freq) % 1.0 < 0.35 else -1.0
        tri = 2.0 * abs(((t * curr_freq) % 1.0) - 0.5) - 1.0
        wave_mix = 0.5 * pulse + 0.5 * tri
        env = 1.0 - math.exp(-30.0 * t) if t < 0.02 else math.exp(-2.5 * (t - 0.02))
        val = vol * env * wave_mix
        samples.append(val)
    return apply_envelope(samples, attack=0.01, decay=0.05, sustain=0.7, release=0.04)

# --- Multi-Track Modern Pop Arrangement Generator ---

def generate_modern_pop_bgm(tempo, bar_chords, lead_melody, bass_pattern):
    """
    Synthesizes a full modern pop song loop with:
    - 4/4 Pop Drum Grooves (Kick, Snare, HiHats)
    - Groovy Synth Bassline
    - Upbeat Chord Stabs
    - Catchy Modern Lead Melody
    """
    beat_sec = 60.0 / tempo
    sixteenth_sec = beat_sec / 4.0
    bar_sec = beat_sec * 4.0
    total_bars = len(bar_chords)
    total_duration = total_bars * bar_sec
    total_samples = int(SAMPLE_RATE * total_duration)
    
    master_buffer = [0.0] * total_samples
    
    def mix_into_buffer(samples, start_time):
        start_idx = int(start_time * SAMPLE_RATE)
        for i in range(len(samples)):
            if start_idx + i < total_samples:
                master_buffer[start_idx + i] += samples[i]

    # 1. Generate 4/4 Pop Drums
    for bar in range(total_bars):
        bar_start = bar * bar_sec
        for beat in range(4):
            beat_start = bar_start + beat * beat_sec
            
            # Kick on beats 1 and 3 (plus syncopated 16th kick on beat 3.5 in chorus)
            if beat in [0, 2]:
                mix_into_buffer(synth_kick(0.14, vol=0.45), beat_start)
            if beat == 3 and bar % 2 == 1:
                mix_into_buffer(synth_kick(0.12, vol=0.35), beat_start + 2 * sixteenth_sec)
                
            # Snare on beats 2 and 4
            if beat in [1, 3]:
                mix_into_buffer(synth_snare(0.14, vol=0.35), beat_start)
                
            # Hi-Hats on every 16th note
            for s16 in range(4):
                h_start = beat_start + s16 * sixteenth_sec
                if s16 == 2 and beat == 3: # Open HiHat accent
                    mix_into_buffer(synth_hihat_open(0.14, vol=0.20), h_start)
                else:
                    vol_hh = 0.22 if s16 % 2 == 0 else 0.14
                    mix_into_buffer(synth_hihat_closed(0.04, vol=vol_hh), h_start)

    # 2. Generate Pop Chord Stabs
    for bar, chord in enumerate(bar_chords):
        bar_start = bar * bar_sec
        # Upbeat pop rhythm: stabs on 1, 1.5, 2.5, 3.5
        stab_offsets = [0.0, 1.5 * beat_sec, 2.5 * beat_sec, 3.5 * beat_sec]
        for offset in stab_offsets:
            dur = 0.22 if offset > 0 else 0.35
            mix_into_buffer(synth_pop_chord_stab(chord, dur, vol=0.16), bar_start + offset)

    # 3. Generate Synth Bass
    for bar in range(total_bars):
        bar_start = bar * bar_sec
        root_note = bass_pattern[bar % len(bass_pattern)]
        # Bouncy bass line rhythm: 1, 1.75, 2.5, 3, 3.75
        bass_rhythms = [
            (0.0, root_note, 0.35),
            (1.5 * beat_sec, root_note, 0.2),
            (2.0 * beat_sec, root_note, 0.3),
            (3.0 * beat_sec, root_note, 0.25)
        ]
        for off, b_note, b_dur in bass_rhythms:
            mix_into_buffer(synth_pop_bass_note(b_note, b_dur, vol=0.32), bar_start + off)

    # 4. Generate Catchy Lead Melody
    curr_time = 0.0
    for note, beats in lead_melody:
        dur = beats * beat_sec
        if note != 'REST':
            mix_into_buffer(synth_pop_lead_note(note, dur, vol=0.25), curr_time)
        curr_time += dur

    # Master Soft Limiter / Clamping
    final_output = []
    for s in master_buffer:
        # Soft compression curve
        clamped = max(-1.0, min(1.0, math.tanh(s * 0.85)))
        final_output.append(clamped)

    return final_output

def generate_all_sounds():
    sound_dir = 'sounds'
    os.makedirs(sound_dir, exist_ok=True)
    
    # SFX
    write_wav(os.path.join(sound_dir, 'sfx_click.wav'), make_sfx_click())
    write_wav(os.path.join(sound_dir, 'sfx_select.wav'), make_sfx_select())
    write_wav(os.path.join(sound_dir, 'sfx_swap.wav'), make_sfx_swap())
    write_wav(os.path.join(sound_dir, 'sfx_match.wav'), make_sfx_match())
    write_wav(os.path.join(sound_dir, 'sfx_combo.wav'), make_sfx_combo())
    write_wav(os.path.join(sound_dir, 'sfx_levelup.wav'), make_sfx_levelup())
    write_wav(os.path.join(sound_dir, 'sfx_gameover.wav'), make_sfx_gameover())
    
    # ----------------------------------------------------
    # Title BGM: Bright, Catchy Modern Pop Title Theme (124 BPM, 8 Bars)
    # Chord Progression: C -> G -> Am -> F -> C -> G -> F -> G
    # ----------------------------------------------------
    title_chords = [
        ['C4', 'E4', 'G4'],  # C
        ['G3', 'B3', 'D4'],  # G
        ['A3', 'C4', 'E4'],  # Am
        ['F3', 'A3', 'C4'],  # F
        ['C4', 'E4', 'G4'],  # C
        ['G3', 'B3', 'D4'],  # G
        ['F3', 'A3', 'C4'],  # F
        ['G3', 'B3', 'D4']   # G
    ]
    title_bass = ['C2', 'G1', 'A1', 'F1', 'C2', 'G1', 'F1', 'G1']
    title_melody = [
        # Bar 1-2: Catchy motif
        ('G5', 0.5), ('E5', 0.5), ('C5', 0.5), ('D5', 0.5),
        ('E5', 1.0), ('G5', 1.0),
        # Bar 3-4: Rise
        ('A5', 0.5), ('G5', 0.5), ('E5', 0.5), ('C5', 0.5),
        ('D5', 1.5), ('REST', 0.5),
        # Bar 5-6: High resolution
        ('G5', 0.5), ('C6', 0.5), ('B5', 0.5), ('A5', 0.5),
        ('G5', 1.0), ('E5', 1.0),
        # Bar 7-8: Pop cadence turn
        ('F5', 0.5), ('G5', 0.5), ('A5', 0.5), ('B5', 0.5),
        ('C6', 1.5), ('REST', 0.5)
    ]
    bgm_title_samples = generate_modern_pop_bgm(124, title_chords, title_melody, title_bass)
    write_wav(os.path.join(sound_dir, 'bgm_title.wav'), bgm_title_samples)

    # ----------------------------------------------------
    # Main BGM: Upbeat, Dynamic Modern Pop Game BGM (132 BPM, 16 Bars)
    # Chord Progression (Verse/Chorus structure):
    # Bars 1-4: F -> G -> Em -> Am
    # Bars 5-8: F -> G -> C -> C7
    # Bars 9-12: F -> G -> Em -> Am
    # Bars 13-16: Dm7 -> G7 -> C -> C
    # ----------------------------------------------------
    main_chords = [
        ['F4', 'A4', 'C5'], ['G4', 'B4', 'D5'], ['E4', 'G4', 'B4'], ['A4', 'C5', 'E5'],
        ['F4', 'A4', 'C5'], ['G4', 'B4', 'D5'], ['C4', 'E4', 'G4'], ['C4', 'E4', 'Bb4'],
        ['F4', 'A4', 'C5'], ['G4', 'B4', 'D5'], ['E4', 'G4', 'B4'], ['A4', 'C5', 'E5'],
        ['D4', 'F4', 'A4', 'C5'], ['G4', 'B4', 'D5'], ['C4', 'E4', 'G4'], ['C4', 'E4', 'G4']
    ]
    main_bass = [
        'F2', 'G2', 'E2', 'A2',
        'F2', 'G2', 'C2', 'C2',
        'F2', 'G2', 'E2', 'A2',
        'D2', 'G2', 'C2', 'C2'
    ]
    main_melody = [
        # Phrase A (Bars 1-4)
        ('C5', 0.5), ('D5', 0.5), ('E5', 0.5), ('G5', 0.5),
        ('A5', 0.75), ('G5', 0.75), ('E5', 0.5),
        ('G5', 0.5), ('E5', 0.5), ('D5', 0.5), ('C5', 0.5),
        ('D5', 1.5), ('REST', 0.5),
        
        # Phrase B (Bars 5-8)
        ('C5', 0.5), ('D5', 0.5), ('E5', 0.5), ('G5', 0.5),
        ('A5', 0.5), ('C6', 0.5), ('B5', 0.5), ('A5', 0.5),
        ('G5', 1.5), ('E5', 0.5),
        ('C5', 1.5), ('REST', 0.5),
        
        # Chorus Peak (Bars 9-12)
        ('A5', 0.5), ('C6', 0.5), ('D6', 0.5), ('E6', 0.5),
        ('D6', 0.75), ('C6', 0.75), ('A5', 0.5),
        ('G5', 0.5), ('A5', 0.5), ('C6', 0.5), ('E6', 0.5),
        ('D6', 1.5), ('REST', 0.5),
        
        # Chorus Resolution (Bars 13-16)
        ('F6', 0.5), ('E6', 0.5), ('D6', 0.5), ('C6', 0.5),
        ('B5', 0.5), ('C6', 0.5), ('D6', 0.5), ('B5', 0.5),
        ('C6', 2.0), ('REST', 1.0)
    ]
    bgm_main_samples = generate_modern_pop_bgm(132, main_chords, main_melody, main_bass)
    write_wav(os.path.join(sound_dir, 'bgm_main.wav'), bgm_main_samples)

if __name__ == '__main__':
    generate_all_sounds()
