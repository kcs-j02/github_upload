/*
 * SPDX-FileCopyrightText: 2010-2022 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: CC0-1.0
 */

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_system.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "sdkconfig.h"
#include <inttypes.h>

static bool is_big_endian() {
  uint16_t ashort = 256u;
  uint8_t *tobyte = (uint8_t *)&ashort;
  if (tobyte[0] == 1 && tobyte[1] == 0) {
    printf("esp32 is big endian!\n");
    return 1;
  } else {
    assert(tobyte[0] == 0 && tobyte[1] == 1);
    printf("esp32 is little endian!\n");
  }
  return 0;
}

char data[] = "\x11\x22\x33\x44\x55\x66\x77\x88\x99\x00";

void sizes() {
  printf("sizeof(null): %u\n", sizeof(NULL));
  printf("sizeof(char): %u\n", sizeof(char));
  printf("sizeof(short): %u\n", sizeof(short));
  printf("sizeof(int): %u\n", sizeof(int));
  printf("sizeof(long int): %u\n", sizeof(long int));
  printf("sizeof(long long int): %u\n", sizeof(long long int));
  printf("sizeof(float): %u\n", sizeof(float));
  printf("sizeof(double): %u\n", sizeof(double));
  printf("sizeof(char *): %u\n", sizeof(char *));
  printf("sizeof(data): %u\n", sizeof(data));
}

void chars() {
  // chars
  char a = '\x63', b = '\x84';

  if (a < b) {
    printf("var a is less than b! char is unsigned!\n");
  } else {
    printf("var a is greater than b! char is SIGNED!!!\n");
  }

  printf("\n");
}

void char_data() {
  printf("data pointer allocated at: %p \n", &data);
  printf("data points to: %p\n", data);
  printf("data contents: %s\n", data);
  for (int i = 0; i < 10; i++) {
    printf("data[%i]: %c as hex: 0x%.02x\n", i, data[i], data[i]);
  }
  printf("\n");
}

void int_data() {
  unsigned int *data_as_int = (unsigned int *)data;
  printf("data_as_int pointer, allocated at: %p \n", &data_as_int);
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
  printf("location: %p, value: %lx\n", l_as_uint32, *l_as_uint32);

  float *l_as_float = (float *)location;
  printf("float location: %p, value: %f\n", l_as_float, *l_as_float);
}

void tests() {
  is_big_endian();
  sizes();
  chars();
  char_data();
  int_data();
  bus();
}

void app_main(void) {
  printf("Hello world!\n");

  tests();

  /* Print chip information */
  esp_chip_info_t chip_info;
  uint32_t flash_size;
  esp_chip_info(&chip_info);
  printf("This is %s chip with %d CPU core(s), %s%s%s%s, ", CONFIG_IDF_TARGET,
         chip_info.cores,
         (chip_info.features & CHIP_FEATURE_WIFI_BGN) ? "WiFi/" : "",
         (chip_info.features & CHIP_FEATURE_BT) ? "BT" : "",
         (chip_info.features & CHIP_FEATURE_BLE) ? "BLE" : "",
         (chip_info.features & CHIP_FEATURE_IEEE802154)
             ? ", 802.15.4 (Zigbee/Thread)"
             : "");

  unsigned major_rev = chip_info.revision / 100;
  unsigned minor_rev = chip_info.revision % 100;
  printf("silicon revision v%d.%d, ", major_rev, minor_rev);
  if (esp_flash_get_size(NULL, &flash_size) != ESP_OK) {
    printf("Get flash size failed");
    return;
  }

  printf("%" PRIu32 "MB %s flash\n", flash_size / (uint32_t)(1024 * 1024),
         (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "embedded"
                                                       : "external");

  printf("Minimum free heap size: %" PRIu32 " bytes\n",
         esp_get_minimum_free_heap_size());

  for (int i = 10; i >= 0; i--) {
    printf("Restarting in %d seconds...\n", i);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
  printf("Restarting now.\n");
  fflush(stdout);
  esp_restart();
}
