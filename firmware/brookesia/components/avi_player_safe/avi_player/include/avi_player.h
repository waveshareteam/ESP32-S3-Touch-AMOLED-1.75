/*
 * SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef __VIDOPLAYER_H
#define __VIDOPLAYER_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "esp_err.h"
#include "esp_idf_version.h"
#include "freertos/FreeRTOS.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    FORMAT_MJEPG = 0,
    FORMAT_H264,
} video_frame_format;

typedef struct {
    uint32_t width;
    uint32_t height;
    video_frame_format frame_format;
} video_frame_info_t;

typedef enum {
    FORMAT_PCM = 0,
} audio_frame_format;

typedef struct {
    uint8_t channel;
    uint8_t bits_per_sample;
    uint32_t sample_rate;
    audio_frame_format format;
} audio_frame_info_t;

typedef enum {
    FRAME_TYPE_VIDEO = 0,
    FRAME_TYPE_AUDIO,
} frame_type_t;

typedef struct {
    uint8_t *data;
    size_t data_bytes;
    frame_type_t type;
    union {
        video_frame_info_t video_info;
        audio_frame_info_t audio_info;
    };
} frame_data_t;

typedef void (*video_write_cb)(frame_data_t *data, void *arg);
typedef void (*audio_write_cb)(frame_data_t *data, void *arg);
typedef void (*audio_set_clock_cb)(uint32_t rate, uint32_t bits_cfg, uint32_t ch, void *arg);
typedef void (*avi_play_end_cb)(void *arg);

typedef void *avi_player_handle_t;

typedef struct {
    size_t buffer_size;
    video_write_cb video_cb;
    audio_write_cb audio_cb;
    audio_set_clock_cb audio_set_clock_cb;
    avi_play_end_cb avi_play_end_cb;
    UBaseType_t priority;
    BaseType_t coreID;
    void *user_data;
    int stack_size;
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 1, 0)
    bool stack_in_psram;
#endif
} avi_player_config_t;

esp_err_t avi_player_play_from_memory(avi_player_handle_t handle, uint8_t *avi_data, size_t avi_size);
esp_err_t avi_player_play_from_file(avi_player_handle_t handle, const char *filename);

esp_err_t avi_player_get_video_buffer(
    avi_player_handle_t handle,
    void **buffer,
    size_t *buffer_size,
    video_frame_info_t *info,
    TickType_t ticks_to_wait
);

esp_err_t avi_player_get_audio_buffer(
    avi_player_handle_t handle,
    void **buffer,
    size_t *buffer_size,
    audio_frame_info_t *info,
    TickType_t ticks_to_wait
);

esp_err_t avi_player_play_stop(avi_player_handle_t handle);
esp_err_t avi_player_init(avi_player_config_t config, avi_player_handle_t *handle);
esp_err_t avi_player_deinit(avi_player_handle_t handle);

#ifdef __cplusplus
}
#endif

#endif
