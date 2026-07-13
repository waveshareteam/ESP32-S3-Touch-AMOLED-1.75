/*
 * Author: Waveshare Eng45
 * Created on: 2024-12-12
 * Description: This code is used to control the LC76G via I2C with the ESP32 chips. The logic is based on the Waveshare Eng45 Raspberry Pi driver for LC76G.
 */
#include "driver/i2c.h"

#define I2C_MASTER_SCL_IO 14
#define I2C_MASTER_SDA_IO 15
#define I2C_MASTER_NUM I2C_NUM_0
#define I2C_MASTER_FREQ_HZ 100000
#define I2C_MASTER_TX_BUF_DISABLE 0
#define I2C_MASTER_RX_BUF_DISABLE 0

#define DEVICE_ADDRESS 0x50
#define DEVICE_ADDRESS_R 0x54
uint8_t readData[4] = { 0 };
void i2c_master_init() {
  i2c_config_t conf = {};
  conf.mode = I2C_MODE_MASTER;
  conf.sda_io_num = I2C_MASTER_SDA_IO;
  conf.scl_io_num = I2C_MASTER_SCL_IO;
  conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
  conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
  conf.master.clk_speed = I2C_MASTER_FREQ_HZ;

  ESP_ERROR_CHECK(i2c_param_config(I2C_MASTER_NUM, &conf));
  ESP_ERROR_CHECK(i2c_driver_install(I2C_MASTER_NUM, conf.mode, I2C_MASTER_RX_BUF_DISABLE, I2C_MASTER_TX_BUF_DISABLE, 0));
}

esp_err_t i2c_write(uint8_t device_addr, const uint8_t *data, size_t data_len) {
  i2c_cmd_handle_t cmd = i2c_cmd_link_create();
  i2c_master_start(cmd);
  i2c_master_write_byte(cmd, (device_addr << 1) | I2C_MASTER_WRITE, true);
  i2c_master_write(cmd, data, data_len, true);
  i2c_master_stop(cmd);
  esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd, pdMS_TO_TICKS(1000));
  i2c_cmd_link_delete(cmd);
  return ret;
}

esp_err_t i2c_read(uint8_t device_addr, uint8_t *data, size_t data_len) {
  i2c_cmd_handle_t cmd = i2c_cmd_link_create();
  i2c_master_start(cmd);
  i2c_master_write_byte(cmd, (device_addr << 1) | I2C_MASTER_READ, true);
  i2c_master_read(cmd, data, data_len, I2C_MASTER_LAST_NACK);
  i2c_master_stop(cmd);
  esp_err_t ret = i2c_master_cmd_begin(I2C_MASTER_NUM, cmd, pdMS_TO_TICKS(1000));
  i2c_cmd_link_delete(cmd);
  return ret;
}

void initwrite() {
  uint8_t data[] = { 0x08, 0x00, 0x51, 0xAA, 0x04, 0x00, 0x00, 0x00 };

  if (i2c_write(DEVICE_ADDRESS, data, sizeof(data)) != ESP_OK) {
    Serial.println("Failed to write data to device");
    return;
  }
  vTaskDelay(pdMS_TO_TICKS(100));

  if (i2c_read(DEVICE_ADDRESS_R, readData, sizeof(readData)) != ESP_OK) {
    Serial.println("Failed to read data from device");
    return;
  }
}

void writeDataToI2C() {
  initwrite();

  uint32_t dataLength = (readData[0]) | (readData[1] << 8) | (readData[2] << 16) | (readData[3] << 24);

  if (dataLength == 0) {
    // Serial.printf("Invalid data length: %u\n", dataLength);
    return;
  }

  uint8_t data2[] = { 0x00, 0x20, 0x51, 0xAA };
  uint8_t dataToSend[sizeof(data2) + sizeof(readData)];
  memcpy(dataToSend, data2, sizeof(data2));
  memcpy(dataToSend + sizeof(data2), readData, sizeof(readData));
  delay(100);

  if (i2c_write(DEVICE_ADDRESS, dataToSend, sizeof(dataToSend)) != ESP_OK) {
    // Serial.println("Failed to write concatenated data");
    return;
  }

  uint8_t *dynamicReadData = (uint8_t *)malloc(dataLength);
  if (!dynamicReadData) {
    // Serial.println("Memory allocation failed");
    return;
  }

  delay(100);

  if (i2c_read(DEVICE_ADDRESS_R, dynamicReadData, dataLength) != ESP_OK) {
    Serial.println("Failed to read dynamic data");
    free(dynamicReadData);
    return;
  }

  String nmeaData = "";
  for (uint32_t i = 0; i < dataLength; i++) {
    nmeaData += (char)dynamicReadData[i];
  }
  Serial.println(nmeaData);

  free(dynamicReadData);
}

void setup() {
  Serial.begin(115200);
  i2c_master_init();
}

void loop() {
  writeDataToI2C();
  delay(500);
}