#include <Arduino.h>
#include <lvgl.h>
#include "Arduino_GFX_Library.h"
#include "lv_conf.h"
#include <Wire.h>
#include <SPI.h>
#include <FS.h>
#include <SD_MMC.h>
#include <stdio.h>  // Optional if not using printf
#include "pin_config.h"

#define EXAMPLE_LVGL_TICK_PERIOD_MS 2
static lv_disp_draw_buf_t draw_buf;
static lv_color_t buf[LCD_WIDTH * LCD_HEIGHT / 10];
lv_obj_t *label;  // Global label object

Arduino_DataBus *bus = new Arduino_ESP32QSPI(
  LCD_CS /* CS */, LCD_SCLK /* SCK */, LCD_SDIO0 /* SDIO0 */, LCD_SDIO1 /* SDIO1 */,
  LCD_SDIO2 /* SDIO2 */, LCD_SDIO3 /* SDIO3 */);

Arduino_CO5300 *gfx = new Arduino_CO5300(
  bus, LCD_RESET /* RST */, 0 /* rotation */, LCD_WIDTH /* width */, LCD_HEIGHT /* height */, 6, 0, 0, 0);


#if LV_USE_LOG != 0
/* Serial debugging */
void my_print(const char *buf) {
  Serial.printf(buf);
  Serial.flush();
}
#endif

void example_lvgl_rounder_cb(struct _lv_disp_drv_t *disp_drv, lv_area_t *area)
{
    if(area->x1 % 2 !=0)area->x1--;
    if(area->y1 % 2 !=0)area->y1--;
    // 变为奇数(如果是偶数就加 1)
    if(area->x2 %2 ==0)area->x2++;
    if(area->y2 %2 ==0)area->y2++;
}


/* Display flushing */
void my_disp_flush(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p) {
  uint32_t w = (area->x2 - area->x1 + 1);
  uint32_t h = (area->y2 - area->y1 + 1);

#if (LV_COLOR_16_SWAP != 0)
  gfx->draw16bitBeRGBBitmap(area->x1, area->y1, (uint16_t *)&color_p->full, w, h);
#else
  gfx->draw16bitRGBBitmap(area->x1, area->y1, (uint16_t *)&color_p->full, w, h);
#endif

  lv_disp_flush_ready(disp);
}

void example_increase_lvgl_tick(void *arg) {
  /* Tell LVGL how many milliseconds has elapsed */
  lv_tick_inc(EXAMPLE_LVGL_TICK_PERIOD_MS);
}

static uint8_t count = 0;
void example_increase_reboot(void *arg) {
  count++;
  if (count == 30) {
    esp_restart();
  }
}

String listDir(fs::FS &fs, const char *dirname, uint8_t levels) {
  Serial.println("Listing directory: " + String(dirname));

  String dirContent = "Listing directory: " + String(dirname) + "\n";

  File root = fs.open(dirname);
  if (!root) {
    Serial.println("Failed to open directory");
    return "Failed to open directory\n";
  }
  if (!root.isDirectory()) {
    Serial.println("Not a directory");
    return "Not a directory\n";
  }

  File file = root.openNextFile();
  while (file) {
    if (file.isDirectory()) {
      String dirName = "  DIR : " + String(file.name()) + "\n";
      Serial.print(dirName);
      dirContent += dirName;
      if (levels) {
        dirContent += listDir(fs, file.path(), levels - 1);
      }
    } else {
      String fileInfo = "  FILE: " + String(file.name()) + "  SIZE: " + String(file.size()) + "\n";
      Serial.print(fileInfo);
      dirContent += fileInfo;
    }
    file = root.openNextFile();
  }
  return dirContent;
}


void setup() {
  Serial.begin(115200);

  Wire.begin(IIC_SDA, IIC_SCL);

  Serial.println("Original status:");
  delay(3000);

  gfx->begin();
  gfx->setBrightness(255);

  lv_init();

  lv_disp_draw_buf_init(&draw_buf, buf, NULL, LCD_WIDTH * LCD_HEIGHT / 10);

  /*Initialize the display*/
  static lv_disp_drv_t disp_drv;
  lv_disp_drv_init(&disp_drv);
  /*Change the following line to your display resolution*/
  disp_drv.hor_res = LCD_WIDTH;
  disp_drv.ver_res = LCD_HEIGHT;
  disp_drv.flush_cb = my_disp_flush;
  disp_drv.rounder_cb = example_lvgl_rounder_cb;
  disp_drv.draw_buf = &draw_buf;
  lv_disp_drv_register(&disp_drv);

  /*Initialize the (dummy) input device driver*/
  static lv_indev_drv_t indev_drv;
  lv_indev_drv_init(&indev_drv);
  indev_drv.type = LV_INDEV_TYPE_POINTER;

  lv_indev_drv_register(&indev_drv);

  const esp_timer_create_args_t lvgl_tick_timer_args = {
    .callback = &example_increase_lvgl_tick,
    .name = "lvgl_tick"
  };

  const esp_timer_create_args_t reboot_timer_args = {
    .callback = &example_increase_reboot,
    .name = "reboot"
  };

  esp_timer_handle_t lvgl_tick_timer = NULL;
  esp_timer_create(&lvgl_tick_timer_args, &lvgl_tick_timer);
  esp_timer_start_periodic(lvgl_tick_timer, EXAMPLE_LVGL_TICK_PERIOD_MS * 1000);

  SD_MMC.setPins(SDMMC_CLK, SDMMC_CMD, SDMMC_DATA);

  lv_obj_t *sd_info_label = lv_label_create(lv_scr_act());
  lv_label_set_long_mode(sd_info_label, LV_LABEL_LONG_WRAP);
  lv_obj_set_width(sd_info_label, 300);
  lv_obj_align(sd_info_label, LV_ALIGN_CENTER, 0, 0);

  if (!SD_MMC.begin("/sdcard", true)) {
    Serial.println("Card Mount Failed");
    lv_label_set_text(sd_info_label, "Card Mount Failed");
  }

  uint8_t cardType = SD_MMC.cardType();
  if (cardType == CARD_NONE) {
    Serial.println("No SD_MMC card attached");
    lv_label_set_text(sd_info_label, "No SD_MMC card attached");
  }

  Serial.print("SD_MMC Card Type: ");
  if (cardType == CARD_MMC) {
    Serial.println("MMC");
  } else if (cardType == CARD_SD) {
    Serial.println("SDSC");
  } else if (cardType == CARD_SDHC) {
    Serial.println("SDHC");
  } else {
    Serial.println("UNKNOWN");
  }

  uint64_t cardSize = SD_MMC.cardSize() / (1024 * 1024);
  Serial.println("SD_MMC Card Size: " + String(cardSize) + "MB");

  char sd_info[256];
  snprintf(sd_info, sizeof(sd_info), "SD_MMC Card Type: %s\nSD_MMC Card Size: %lluMB\n",
           cardType == CARD_MMC ? "MMC" : cardType == CARD_SD   ? "SDSC"
                                        : cardType == CARD_SDHC ? "SDHC"
                                                                : "UNKNOWN",
           cardSize);

  String dirList = listDir(SD_MMC, "/", 0);
  strncat(sd_info, dirList.c_str(), sizeof(sd_info) - strlen(sd_info) - 1);

  lv_label_set_text(sd_info_label, sd_info);
}

void loop() {
  lv_timer_handler(); /* let the GUI do its work */
  delay(5);
}
