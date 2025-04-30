# CryptoBro en détresse

This challenge gives us the power consumption of a "something" that validates PIN codes.
We will be going towards differential power analysis (DPA) to solve this problem.

Initially I tried calculating the mean for all the numbers at the same time, but nothing stood out particularly. So I imagined that the code that checked the PIN was probably checking the numbers one by one. So we are going to proceed the same way.

We calculated the average power consumption for all the codes that started with `0???` then all those like `1???`... and compared their averages, the one that stood out the furthest from the lot gives us the right first digit.

We got this output

```txt
Analyzing digit position 1...
Digit 0 difference score: 0.065464
Digit 1 difference score: 0.057082
Digit 2 difference score: 0.063797
Digit 3 difference score: 0.053306
Digit 4 difference score: 0.057586
Digit 5 difference score: 0.057638
Digit 6 difference score: 0.053020
Digit 7 difference score: 0.053250
Digit 8 difference score: 0.062998
Digit 9 difference score: 0.524083
Most likely digit at position 1: 9 (score: 0.524083)
```

This was quite promising as 9 was ten times further from the average than the rest of the digits. So we went on for the second step similarly comparing all the traces of `90??`, `91??`...

And so on and so forth until the end where we just compared `9460`, `9461`, `9462`...

Which gave us the flag.

The code to do this is the following

```python
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

PLOT = False

traces_dir: Path = Path('traces')
trace_files: list[Path] = sorted(list(traces_dir.glob('trace_*.npy')))

all_traces: list[np.ndarray] = []
all_pins: list[str] = []
for trace_path in trace_files:
    pin: str = trace_path.stem.split('_')[1]
    trace: np.ndarray = np.load(trace_path)
    all_traces.append(trace)
    all_pins.append(pin)

all_traces_array: np.ndarray = np.array(all_traces)
print(f'Loaded {len(all_traces)} traces, shape: {all_traces_array.shape}')


def digit_by_digit_dpa() -> str:
    print('\nPerforming digit-by-digit DPA analysis...')
    pin_length: int = len(all_pins[0])
    recovered_pin: str = ''

    for position in range(pin_length):
        print(f'\nAnalyzing digit position {position+1}...')

        filtered_indices: list[int] | range
        filtered_indices = range(len(all_pins))
        if position > 0:
            filtered_indices = [i for i, pin in enumerate(all_pins) if pin.startswith(recovered_pin)]
            print(f'Narrowed down to {len(filtered_indices)} candidates starting with {recovered_pin}')

        max_diff_score: float = -1
        best_digit: int | None = None

        for digit in range(10):
            digit_indices: list[int] = [i for i in filtered_indices if all_pins[i][position] == str(digit)]

            if not digit_indices:
                continue

            other_indices: list[int] = [i for i in filtered_indices if all_pins[i][position] != str(digit)]

            if not other_indices:
                continue

            digit_avg: np.ndarray = np.mean(all_traces_array[digit_indices], axis=0)
            other_avg: np.ndarray = np.mean(all_traces_array[other_indices], axis=0)

            diff: np.ndarray = digit_avg - other_avg

            diff_score: float = np.max(np.abs(diff))

            print(f'Digit {digit} difference score: {diff_score:.6f}')

            if PLOT:
                plt.figure(figsize=(12, 6))
                plt.plot(diff)
                plt.title(f'Difference for digit {digit} at position {position+1}')
                plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
                plt.savefig(f'diffs/diff_pos{position+1}_digit{digit}.png')
                plt.close()

            if diff_score > max_diff_score:
                max_diff_score = diff_score
                best_digit = digit

        if best_digit is not None:
            recovered_pin += str(best_digit)
            print(f'Most likely digit at position {position+1}: {best_digit} (score: {max_diff_score:.6f})')
        else:
            print(f'Could not determine digit at position {position+1}')
            break

    return recovered_pin


recovered_pin: str = digit_by_digit_dpa()

print(f'\nRecovered PIN: {recovered_pin}')
print(f'Flag: FCSC{{{recovered_pin}}}')

```
