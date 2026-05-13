#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "driver/i2c.h"
#include "esp_err.h"
#include "esp_log.h"

#define I2C_PORT I2C_NUM_0


#define SDA_PIN 1
#define SCL_PIN 0

#define I2C_FREQ_HZ 100000

#define RPR_ADDR 0x38

#define REG_MODE_CONTROL   0x41
#define REG_ALS0_DATA_LSB  0x46

static const char *TAG = "RPR0521";

static esp_err_t i2c_init(void)
{
    i2c_config_t conf = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = SDA_PIN,
        .scl_io_num = SCL_PIN,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = I2C_FREQ_HZ,
    };

    ESP_ERROR_CHECK(i2c_param_config(I2C_PORT, &conf));
    return i2c_driver_install(I2C_PORT, I2C_MODE_MASTER, 0, 0, 0);
}

static esp_err_t write_reg(uint8_t reg, uint8_t val)
{
    uint8_t data[2] = {reg, val};

    return i2c_master_write_to_device(
        I2C_PORT,
        RPR_ADDR,
        data,
        2,
        pdMS_TO_TICKS(1000)
    );
}

static esp_err_t read_reg(uint8_t reg, uint8_t *data, size_t len)
{
    return i2c_master_write_read_device(
        I2C_PORT,
        RPR_ADDR,
        &reg,
        1,
        data,
        len,
        pdMS_TO_TICKS(1000)
    );
}

static void i2c_scan(void)
{
    printf("I2C scan start\n");

    bool found = false;

    for (uint8_t addr = 1; addr < 127; addr++) {
        esp_err_t ret = i2c_master_write_to_device(
            I2C_PORT,
            addr,
            NULL,
            0,
            pdMS_TO_TICKS(50)
        );

        if (ret == ESP_OK) {
            found = true;
            printf("Found I2C device: 0x%02X\n", addr);
        }
    }

    if (!found) {
        printf("No I2C device found\n");
    }

    printf("----------------\n");
}

static esp_err_t rpr_init(void)
{
    return write_reg(REG_MODE_CONTROL, 0xC6);
}

static esp_err_t read_rpr(uint16_t *als0, uint16_t *als1, float *lux)
{
    uint8_t data[4];

    esp_err_t ret = read_reg(REG_ALS0_DATA_LSB, data, 4);
    if (ret != ESP_OK) {
        return ret;
    }

    *als0 = data[0] | (data[1] << 8);
    *als1 = data[2] | (data[3] << 8);

    if (*als0 == 0) {
        *lux = 0;
        return ESP_OK;
    }

    float ratio = (float)(*als1) / (float)(*als0);

    if (ratio < 0.595) {
        *lux = 1.682f * (*als0) - 1.877f * (*als1);
    } else if (ratio < 1.015) {
        *lux = 0.644f * (*als0) - 0.132f * (*als1);
    } else if (ratio < 1.352) {
        *lux = 0.756f * (*als0) - 0.243f * (*als1);
    } else if (ratio < 3.053) {
        *lux = 0.766f * (*als0) - 0.250f * (*als1);
    } else {
        *lux = 0;
    }

    return ESP_OK;
}

void app_main(void)
{
    printf("ESP-IDF RPR-0521RS start\n");

    if (i2c_init() != ESP_OK) {
        ESP_LOGE(TAG, "I2C init failed");
        return;
    }

    printf("I2C init OK\n");

    if (rpr_init() != ESP_OK) {
        ESP_LOGE(TAG, "RPR-0521RS init failed");
        return;
    }

    printf("RPR-0521RS init OK\n");

    while (1) {
        uint16_t als0, als1;
        float lux;

        if (read_rpr(&als0, &als1, &lux) == ESP_OK) {
            printf("ALS0=%u  ALS1=%u  Light=%.2f lux\n", als0, als1, lux);
        } else {
            ESP_LOGE(TAG, "RPR-0521RS read failed");
        }

        vTaskDelay(pdMS_TO_TICKS(15000));
    }
}