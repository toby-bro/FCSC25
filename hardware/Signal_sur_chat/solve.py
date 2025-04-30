import os

import numpy as np
from Gold import Gold
from scipy.io import wavfile

# Thanks to https://github.com/chrinels/sequences


LFSR_LEN = 15
SEQ_LEN = (1 << LFSR_LEN) - 1  # 32767
INIT_STATE = [int(x) for x in format(0x7FFF, f'0{LFSR_LEN}b')]
TAPS1 = [15, 7, 0]  # x^15 + x^7 + 1
TAPS2 = [15, 10, 5, 4, 0]  # x^15 + x^10 + x^5 + x^4 + 1
PHASES = [4, 7, 8, 24, 27, 31, 39, 42, 43, 49, 53, 54, 59, 62, 65, 73, 93, 99, 118, 119, 120, 128]
BITS_PER_CHAR = 8
AUDIO_FILE = 'signal-sur-chat.wav'
PLOT = False


def transform_gold_code(gold_code: np.ndarray) -> np.ndarray:
    return np.where(gold_code == 1, -0.5, 0.5)


def decode_signal(audio_data: np.ndarray, phases: list[int]) -> str:
    flag = ''
    samples_per_bit = SEQ_LEN

    for idx, phase in enumerate(phases):
        gold_generator = Gold(TAPS1, INIT_STATE, TAPS2, INIT_STATE, index=phase)
        gold_code = gold_generator.step()

        gold_code_corr = transform_gold_code(np.array(gold_code))

        bits = []
        for bit_index in range(BITS_PER_CHAR):
            start = bit_index * samples_per_bit
            end = start + samples_per_bit
            segment = audio_data[start:end]

            correlation = float(np.sum(segment * gold_code_corr[: len(segment)]))

            bit = '1' if correlation > 0 else '0'
            bits.append(bit)

        char_val = int(''.join(bits), 2)
        try:
            char = chr(char_val)
            flag += char
        except Exception:
            flag += '?'

        print(
            f"Char {idx+1:2d} (phase={phase:3d}): bits={''.join(bits)} -> {char if 32 <= char_val < 127 else '?'}",
        )

    return flag


if __name__ == '__main__':
    gold_generator = Gold(TAPS1, INIT_STATE, TAPS2, INIT_STATE, index=128)

    if not os.path.exists(AUDIO_FILE):
        print(f"Error: Audio file '{AUDIO_FILE}' not found.")
        exit(1)

    print(f'Reading audio file: {AUDIO_FILE}...')
    sample_rate, audio_data_raw = wavfile.read(AUDIO_FILE)
    audio_data = audio_data_raw.astype(np.float64)
    if audio_data.ndim > 1:
        audio_data = audio_data[:, 0]

    print(f'Audio read: {len(audio_data)} samples, Sample rate: {sample_rate} Hz')
    if len(audio_data) != BITS_PER_CHAR * SEQ_LEN:
        print(f'Warning: audio length {len(audio_data)} != expected {BITS_PER_CHAR * SEQ_LEN}')

    flag = decode_signal(audio_data, PHASES)
    print(f'\nFlag: {flag}')
