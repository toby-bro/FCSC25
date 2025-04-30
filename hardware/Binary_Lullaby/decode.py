def decode_output(input_filepath: str = 'output.txt') -> str:
    decoded_string = ''

    with open(input_filepath, 'r') as f:
        for line in f:
            binary_string = line.strip()
            if len(binary_string) == 16:
                try:
                    char1_bin = binary_string[0:8]
                    char2_bin = binary_string[8:16]

                    char1 = chr(int(char1_bin, 2))
                    char2 = chr(int(char2_bin, 2))

                    decoded_string += char1 + char2
                except ValueError:
                    print(f'Skipping invalid binary line: {binary_string}')
                except OverflowError:
                    print(f'Skipping value out of ASCII range: {binary_string}')
            elif binary_string:
                print(f'Skipping line with incorrect length ({len(binary_string)} bits): {binary_string}')

    return decoded_string


if __name__ == '__main__':
    result = decode_output()
    if result is not None:
        print('Decoded Result:')
        print(result)
