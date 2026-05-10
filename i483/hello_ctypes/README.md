| Supported Targets | ESP32 | ESP32-C2 | ESP32-C3 | ESP32-C5 | ESP32-C6 | ESP32-C61 | ESP32-H2 | ESP32-P4 | ESP32-S2 | ESP32-S3 | Linux |
| ----------------- | ----- | -------- | -------- | -------- | -------- | --------- | -------- | -------- | -------- | -------- | ----- |

# Hello World Example

Starts a FreeRTOS task to print "Hello World".

(See the README.md file in the upper level 'examples' directory for more information about examples.)

## How to use example

Follow detailed instructions provided specifically for this example.

Select the instructions depending on Espressif chip installed on your development board:

- [ESP32 Getting Started Guide](https://docs.espressif.com/projects/esp-idf/en/stable/get-started/index.html)
- [ESP32-S2 Getting Started Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32s2/get-started/index.html)


## Example folder contents

The project **hello_world** contains one source file in C language [hello_world_main.c](main/hello_world_main.c). The file is located in folder [main](main).

ESP-IDF projects are built using CMake. The project build configuration is contained in `CMakeLists.txt` files that provide set of directives and instructions describing the project's source files and targets (executable, library, or both).

Below is short explanation of remaining files in the project folder.

```
├── CMakeLists.txt
├── pytest_hello_world.py      Python script used for automated testing
├── main
│   ├── CMakeLists.txt
│   └── hello_world_main.c
└── README.md                  This is the file you are currently reading
```

For more information on structure and contents of ESP-IDF projects, please refer to Section [Build System](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/build-system.html) of the ESP-IDF Programming Guide.

## Troubleshooting

* Program upload failure

    * Hardware connection is not correct: run `idf.py -p PORT monitor`, and reboot your board to see if there are any output logs.
    * The baud rate for downloading is too high: lower your baud rate in the `menuconfig` menu, and try again.

## Technical support and feedback

Please use the following feedback channels:

* For technical queries, go to the [esp32.com](https://esp32.com/) forum
* For a feature request or bug report, create a [GitHub issue](https://github.com/espressif/esp-idf/issues)

We will get back to you as soon as possible.


## result!!

linux x86 is little endian!
sizeof(null): 8
sizeof(char): 1
sizeof(short): 2
sizeof(int): 4
sizeof(long int): 4
sizeof(long long int): 8
sizeof(float): 4
sizeof(double): 8
sizeof(char *): 8
sizeof(size_t): 8
sizeof(ssize_t): 8
sizeof(data): 11
sizeof(data_p): 8

var a is greater than b! char is SIGNED!!!

data allocated at: 00007FF7D5CB4010 
data points to: 00007FF7D5CB4010
data contents: "3DUfw・
data[0]:  as hex: 0x11
data[1]: " as hex: 0x22
data[2]: 3 as hex: 0x33
data[3]: D as hex: 0x44
data[4]: U as hex: 0x55
data[5]: f as hex: 0x66
data[6]: w as hex: 0x77
data[7]: ・as hex: 0xffffff88
data[8]: ・as hex: 0xffffff99
data[9]:  as hex: 0x00

data_as_int, allocated at: 000000762C9FF7D0 
data as int points to: 00007FF7D5CB4010
data_as_int[0]: 44332211
data_as_int[1]: 88776655
data_as_int[2]: 99

location: 00007FF7D5CB4011, value: 55443322
float location: 00007FF7D5CB4011, value: 13482743300096.000000

