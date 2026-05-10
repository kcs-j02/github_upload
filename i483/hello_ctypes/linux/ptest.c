#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

char data[] = "\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00";
char *data_p = data;

void is_big_endian() {
  short number = 256u;
  uint8_t *as_bytes = (uint8_t *)&number;
  if (as_bytes[0] == 1 && as_bytes[1] == 0) {
    printf("linux x86 is big endian???\n");
  } else {
    assert(as_bytes[0] == 0 && as_bytes[1] == 1);
    printf("linux x86 is little endian!\n");
  }
}

void sizes() {
  printf("sizeof(null): %lu\n", sizeof(NULL));
  printf("sizeof(char): %lu\n", sizeof(char));
  printf("sizeof(short): %lu\n", sizeof(short));
  printf("sizeof(int): %lu\n", sizeof(int));
  printf("sizeof(long int): %lu\n", sizeof(long int));
  printf("sizeof(long long int): %lu\n", sizeof(long long int));
  printf("sizeof(float): %lu\n", sizeof(float));
  printf("sizeof(double): %lu\n", sizeof(double));
  printf("sizeof(char *): %lu\n", sizeof(char *));
  printf("sizeof(size_t): %lu\n", sizeof(size_t));
  printf("sizeof(ssize_t): %lu\n", sizeof(ssize_t));
  printf("sizeof(data): %lu\n", sizeof(data));
  printf("sizeof(data_p): %lu\n\n", sizeof(data_p));
}

void chars() {
  // chars
  char a = '\x63', b = '\x84';

  if (a < b) {
    printf("var a is less than b, char is unsigned!\n");
  } else {
    printf("var a is greater than b! char is SIGNED!!!\n");
  }

  printf("\n");
}

void char_data() {
  printf("data allocated at: %p \n", &data);
  printf("data points to: %p\n", data);
  printf("data contents: %s\n", data);
  for (int i = 0; i < 10; i++) {
    printf("data[%i]: %c as hex: 0x%.02x\n", i, data[i], data[i]);
  }
  printf("\n");
}

void int_data() {
  unsigned int *data_as_int = (unsigned int *)data;
  printf("data_as_int, allocated at: %p \n", &data_as_int);
  printf("data as int points to: %p\n", data_as_int);
  for (int i = 0; i < 3; i++) {
    printf("data_as_int[%d]: %x\n", i, data_as_int[i]);
  }
  printf("\n");
}

void bus() {
  char *location = data;
  location++;
  uint32_t *l_as_uint32 = (uint32_t *)location;
  printf("location: %p, value: %x\n", l_as_uint32, *l_as_uint32);

  float *l_as_float = (float *)location;
  printf("float location: %p, value: %f\n", l_as_float, *l_as_float);
}

int main(int argc, char *argv[]) {
  is_big_endian();
  sizes();
  chars();
  char_data();
  int_data();
  bus();
}
