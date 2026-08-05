/*
 * SPDX-FileCopyrightText: 2024-2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "avi_player.h"

#include <inttypes.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "avifile.h"
#include "esp_check.h"
#include "esp_err.h"
#include "esp_heap_caps.h"
#include "esp_idf_version.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/event_groups.h"
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 1, 0)
#include "freertos/idf_additions.h"
#endif
#include "freertos/semphr.h"
#include "freertos/task.h"

static const char *TAG = "avi player";

#define EVENT_FPS_TIME_UP     BIT0
#define EVENT_START_PLAY      BIT1
#define EVENT_STOP_PLAY       BIT2
#define EVENT_DEINIT          BIT3
#define EVENT_DEINIT_DONE     BIT4
#define EVENT_VIDEO_BUF_READY BIT5
#define EVENT_AUDIO_BUF_READY BIT6

#define EVENT_WORKER_INPUT (EVENT_FPS_TIME_UP | EVENT_START_PLAY | EVENT_STOP_PLAY | EVENT_DEINIT)
#define EVENT_FRAME_READY  (EVENT_VIDEO_BUF_READY | EVENT_AUDIO_BUF_READY)

typedef enum {
    PLAY_FILE,
    PLAY_MEMORY,
} play_mode_t;

typedef enum {
    AVI_PARSER_NONE,
    AVI_PARSER_HEADER,
    AVI_PARSER_DATA,
} avi_play_state_t;

typedef struct {
    play_mode_t mode;
    union {
        struct {
            uint8_t *data;
            uint32_t size;
            uint32_t read_offset;
        } memory;
        struct {
            FILE *avi_file;
        } file;
    };
    uint8_t *pbuffer;
    uint32_t str_size;
    uint32_t movi_bytes_read;
    avi_play_state_t state;
    avi_typedef AVI_file;
} avi_data_t;

typedef struct {
    EventGroupHandle_t event_group;
    SemaphoreHandle_t state_mutex;
    SemaphoreHandle_t buffer_mutex;
    esp_timer_handle_t timer_handle;
    TaskHandle_t task_handle;
    avi_player_config_t config;
    avi_data_t avi_data;
    bool play_active;
    bool stop_requested;
    bool deinit_requested;
    bool timer_running;
} avi_player_t;

typedef struct {
    uint32_t fourcc;
    uint32_t data_size;
    uint32_t padded_size;
} avi_frame_t;

static bool take_mutex(SemaphoreHandle_t mutex)
{
    return mutex != NULL && xSemaphoreTake(mutex, portMAX_DELAY) == pdTRUE;
}

static void give_mutex(SemaphoreHandle_t mutex)
{
    if (mutex != NULL) {
        xSemaphoreGive(mutex);
    }
}

static bool playback_cancel_requested(avi_player_t *player)
{
    bool requested = true;
    if (take_mutex(player->state_mutex)) {
        requested = player->stop_requested || player->deinit_requested;
        give_mutex(player->state_mutex);
    }
    return requested;
}

static bool playback_is_active(avi_player_t *player)
{
    bool active = false;
    if (take_mutex(player->state_mutex)) {
        active = player->play_active;
        give_mutex(player->state_mutex);
    }
    return active;
}

static esp_err_t read_exact(FILE *file, void *buffer, size_t size, const char *description)
{
    uint8_t *output = (uint8_t *)buffer;
    size_t total = 0;
    while (total < size) {
        const size_t current = fread(output + total, 1, size - total, file);
        total += current;
        if (current == 0) {
            ESP_LOGE(TAG, "%s short read: %u/%u bytes%s", description,
                     (unsigned)total, (unsigned)size, ferror(file) ? " (I/O error)" : " (EOF)");
            return ferror(file) ? ESP_FAIL : ESP_ERR_INVALID_SIZE;
        }
    }
    if (ferror(file)) {
        ESP_LOGE(TAG, "%s read completed with an I/O error", description);
        return ESP_FAIL;
    }
    return ESP_OK;
}

static esp_err_t read_frame(avi_player_t *player, avi_frame_t *frame)
{
    avi_data_t *avi = &player->avi_data;
    AVI_CHUNK_HEAD head = {0};

    if (avi->movi_bytes_read > avi->AVI_file.movi_size ||
        avi->AVI_file.movi_size - avi->movi_bytes_read < sizeof(head)) {
        return ESP_ERR_INVALID_SIZE;
    }

    if (avi->mode == PLAY_MEMORY) {
        if (avi->memory.read_offset > avi->memory.size ||
            sizeof(head) > avi->memory.size - avi->memory.read_offset) {
            ESP_LOGE(TAG, "Not enough memory data for AVI chunk header");
            return ESP_ERR_INVALID_SIZE;
        }
        memcpy(&head, avi->memory.data + avi->memory.read_offset, sizeof(head));
        avi->memory.read_offset += sizeof(head);
    } else {
        if (avi->file.avi_file == NULL) {
            return ESP_ERR_INVALID_STATE;
        }
        esp_err_t result = read_exact(avi->file.avi_file, &head, sizeof(head), "AVI chunk header");
        if (result != ESP_OK) {
            return result;
        }
    }

    const uint64_t padded_size = (uint64_t)head.size + (head.size & 1U);
    const uint64_t consumed = sizeof(head) + padded_size;
    const uint32_t remaining = avi->AVI_file.movi_size - avi->movi_bytes_read;
    if (padded_size > player->config.buffer_size || consumed > remaining ||
        padded_size > UINT32_MAX) {
        ESP_LOGE(TAG, "Invalid AVI chunk 0x%08" PRIx32 " size %" PRIu32,
                 head.FourCC, head.size);
        return ESP_ERR_INVALID_SIZE;
    }

    if (padded_size != 0) {
        if (avi->mode == PLAY_MEMORY) {
            if (avi->memory.read_offset > avi->memory.size ||
                padded_size > avi->memory.size - avi->memory.read_offset) {
                ESP_LOGE(TAG, "Not enough memory data for AVI chunk payload");
                return ESP_ERR_INVALID_SIZE;
            }
            memcpy(avi->pbuffer, avi->memory.data + avi->memory.read_offset, (size_t)padded_size);
            avi->memory.read_offset += (uint32_t)padded_size;
        } else {
            esp_err_t result = read_exact(
                avi->file.avi_file,
                avi->pbuffer,
                (size_t)padded_size,
                "AVI chunk payload"
            );
            if (result != ESP_OK) {
                return result;
            }
        }
    }

    avi->movi_bytes_read += (uint32_t)consumed;
    avi->str_size = head.size;
    frame->fourcc = head.FourCC;
    frame->data_size = head.size;
    frame->padded_size = (uint32_t)padded_size;
    return ESP_OK;
}

static esp_err_t stop_timer(avi_player_t *player)
{
    if (!player->timer_running || player->timer_handle == NULL) {
        return ESP_OK;
    }
    const esp_err_t result = esp_timer_stop(player->timer_handle);
    player->timer_running = false;
    return result == ESP_ERR_INVALID_STATE ? ESP_OK : result;
}

static esp_err_t finish_playback(avi_player_t *player, bool notify_end)
{
    esp_err_t result = stop_timer(player);
    if (result != ESP_OK) {
        ESP_LOGW(TAG, "Could not stop AVI timer: %s", esp_err_to_name(result));
    }

    FILE *file = NULL;
    if (player->avi_data.mode == PLAY_FILE) {
        file = player->avi_data.file.avi_file;
        player->avi_data.file.avi_file = NULL;
    } else {
        player->avi_data.memory.data = NULL;
        player->avi_data.memory.size = 0;
        player->avi_data.memory.read_offset = 0;
    }

    if (file != NULL && fclose(file) != 0) {
        ESP_LOGW(TAG, "Closing AVI file reported an I/O error");
        if (result == ESP_OK) {
            result = ESP_FAIL;
        }
    }

    bool was_active = false;
    if (take_mutex(player->state_mutex)) {
        was_active = player->play_active;
        player->play_active = false;
        player->stop_requested = false;
        player->avi_data.state = AVI_PARSER_NONE;
        give_mutex(player->state_mutex);
    }

    if (take_mutex(player->buffer_mutex)) {
        player->avi_data.str_size = 0;
        player->avi_data.movi_bytes_read = 0;
        memset(&player->avi_data.AVI_file, 0, sizeof(player->avi_data.AVI_file));
        give_mutex(player->buffer_mutex);
    }
    xEventGroupClearBits(player->event_group, EVENT_FPS_TIME_UP | EVENT_START_PLAY |
                        EVENT_STOP_PLAY | EVENT_FRAME_READY);

    if (notify_end && was_active && player->config.avi_play_end_cb != NULL) {
        player->config.avi_play_end_cb(player->config.user_data);
    }
    return result;
}

static esp_err_t parse_header(avi_player_t *player)
{
    if (playback_cancel_requested(player)) {
        return ESP_ERR_INVALID_STATE;
    }

    size_t bytes_read = 0;
    if (!take_mutex(player->buffer_mutex)) {
        return ESP_FAIL;
    }

    if (player->avi_data.mode == PLAY_MEMORY) {
        bytes_read = player->avi_data.memory.size < player->config.buffer_size
                         ? player->avi_data.memory.size
                         : player->config.buffer_size;
        if (bytes_read != 0) {
            memcpy(player->avi_data.pbuffer, player->avi_data.memory.data, bytes_read);
        }
    } else {
        FILE *file = player->avi_data.file.avi_file;
        if (file == NULL) {
            give_mutex(player->buffer_mutex);
            return ESP_ERR_INVALID_STATE;
        }
        clearerr(file);
        bytes_read = fread(player->avi_data.pbuffer, 1, player->config.buffer_size, file);
        if (ferror(file)) {
            ESP_LOGE(TAG, "AVI header read failed after %u bytes", (unsigned)bytes_read);
            give_mutex(player->buffer_mutex);
            return ESP_FAIL;
        }
    }

    if (bytes_read == 0 || bytes_read > UINT32_MAX) {
        give_mutex(player->buffer_mutex);
        return ESP_ERR_INVALID_SIZE;
    }
    const int parser_result = avi_parser(
        &player->avi_data.AVI_file,
        player->avi_data.pbuffer,
        (uint32_t)bytes_read
    );
    if (parser_result < 0) {
        if (bytes_read == player->config.buffer_size) {
            ESP_LOGE(TAG,
                     "AVI header is invalid, incomplete, or exceeds buffer_size (%u bytes); "
                     "increase avi_player_config_t.buffer_size",
                     (unsigned)player->config.buffer_size);
        } else {
            ESP_LOGE(TAG, "AVI header is invalid or truncated (%u bytes, parser %d)",
                     (unsigned)bytes_read, parser_result);
        }
        give_mutex(player->buffer_mutex);
        return ESP_ERR_INVALID_SIZE;
    }

    const uint32_t movi_start = player->avi_data.AVI_file.movi_start;
    const uint32_t movi_size = player->avi_data.AVI_file.movi_size;
    const uint16_t fps = player->avi_data.AVI_file.vids_fps;
    const uint16_t audio_rate = player->avi_data.AVI_file.auds_sample_rate;
    const uint16_t audio_bits = player->avi_data.AVI_file.auds_bits;
    const uint16_t audio_channels = player->avi_data.AVI_file.auds_channels;

    if (movi_size == 0 || fps == 0) {
        give_mutex(player->buffer_mutex);
        return ESP_ERR_INVALID_SIZE;
    }
    if (player->avi_data.mode == PLAY_MEMORY) {
        if (movi_start > player->avi_data.memory.size ||
            movi_size > player->avi_data.memory.size - movi_start) {
            ESP_LOGE(TAG, "AVI movi range exceeds the memory buffer");
            give_mutex(player->buffer_mutex);
            return ESP_ERR_INVALID_SIZE;
        }
        player->avi_data.memory.read_offset = movi_start;
    } else {
        if (movi_start > LONG_MAX ||
            fseek(player->avi_data.file.avi_file, (long)movi_start, SEEK_SET) != 0) {
            ESP_LOGE(TAG, "Could not seek to AVI movi payload");
            give_mutex(player->buffer_mutex);
            return ESP_FAIL;
        }
    }
    player->avi_data.movi_bytes_read = 0;
    player->avi_data.state = AVI_PARSER_DATA;
    give_mutex(player->buffer_mutex);

    if (playback_cancel_requested(player)) {
        return ESP_ERR_INVALID_STATE;
    }
    if (player->config.audio_set_clock_cb != NULL && audio_rate != 0) {
        player->config.audio_set_clock_cb(
            audio_rate,
            audio_bits,
            audio_channels,
            player->config.user_data
        );
    }

    uint64_t period_us = 1000000ULL / fps;
    if (period_us == 0) {
        period_us = 1;
    }
    const esp_err_t timer_result = esp_timer_start_periodic(player->timer_handle, period_us);
    if (timer_result != ESP_OK) {
        ESP_LOGE(TAG, "Could not start AVI timer: %s", esp_err_to_name(timer_result));
        return timer_result;
    }
    player->timer_running = true;
    return ESP_OK;
}

static esp_err_t process_frames(avi_player_t *player, bool *playback_ended)
{
    *playback_ended = false;
    while (!playback_cancel_requested(player)) {
        if (player->avi_data.movi_bytes_read == player->avi_data.AVI_file.movi_size) {
            *playback_ended = true;
            return ESP_OK;
        }

        avi_frame_t frame = {0};
        if (!take_mutex(player->buffer_mutex)) {
            return ESP_FAIL;
        }
        const esp_err_t read_result = read_frame(player, &frame);
        give_mutex(player->buffer_mutex);
        if (read_result != ESP_OK) {
            return read_result;
        }

        ESP_LOGD(TAG, "type=%08" PRIx32 ", size=%" PRIu32, frame.fourcc, frame.data_size);
        if ((frame.fourcc & 0xFFFF0000U) == DC_ID) {
            if (player->config.video_cb != NULL) {
                frame_data_t data = {
                    .data = player->avi_data.pbuffer,
                    .data_bytes = frame.data_size,
                    .type = FRAME_TYPE_VIDEO,
                    .video_info = {
                        .width = player->avi_data.AVI_file.vids_width,
                        .height = player->avi_data.AVI_file.vids_height,
                        .frame_format = player->avi_data.AVI_file.vids_format,
                    },
                };
                player->config.video_cb(&data, player->config.user_data);
            }
            xEventGroupSetBits(player->event_group, EVENT_VIDEO_BUF_READY);
            if (player->avi_data.movi_bytes_read == player->avi_data.AVI_file.movi_size) {
                *playback_ended = true;
            }
            return ESP_OK;
        }

        if ((frame.fourcc & 0xFFFF0000U) == WB_ID) {
            if (player->config.audio_cb != NULL) {
                frame_data_t data = {
                    .data = player->avi_data.pbuffer,
                    .data_bytes = frame.data_size,
                    .type = FRAME_TYPE_AUDIO,
                    .audio_info = {
                        .channel = player->avi_data.AVI_file.auds_channels,
                        .bits_per_sample = player->avi_data.AVI_file.auds_bits,
                        .sample_rate = player->avi_data.AVI_file.auds_sample_rate,
                        .format = FORMAT_PCM,
                    },
                };
                player->config.audio_cb(&data, player->config.user_data);
            }
            xEventGroupSetBits(player->event_group, EVENT_AUDIO_BUF_READY);
            continue;
        }

        ESP_LOGE(TAG, "Unsupported AVI chunk 0x%08" PRIx32, frame.fourcc);
        return ESP_ERR_NOT_SUPPORTED;
    }
    return ESP_ERR_INVALID_STATE;
}

static void avi_player_task(void *args)
{
    avi_player_t *player = (avi_player_t *)args;
    bool exit_task = false;

    while (!exit_task) {
        const EventBits_t bits = xEventGroupWaitBits(
            player->event_group,
            EVENT_WORKER_INPUT,
            pdTRUE,
            pdFALSE,
            portMAX_DELAY
        );

        if ((bits & EVENT_DEINIT) != 0) {
            (void)finish_playback(player, true);
            exit_task = true;
            continue;
        }

        if ((bits & EVENT_STOP_PLAY) != 0) {
            (void)finish_playback(player, true);
            continue;
        }

        if ((bits & EVENT_START_PLAY) != 0) {
            const esp_err_t result = parse_header(player);
            if (result != ESP_OK) {
                if (result != ESP_ERR_INVALID_STATE) {
                    ESP_LOGE(TAG, "AVI start failed: %s", esp_err_to_name(result));
                }
                (void)finish_playback(player, true);
            }
            continue;
        }

        if ((bits & EVENT_FPS_TIME_UP) != 0 && playback_is_active(player)) {
            bool playback_ended = false;
            const esp_err_t result = process_frames(player, &playback_ended);
            if (result != ESP_OK || playback_ended) {
                if (result != ESP_OK && result != ESP_ERR_INVALID_STATE) {
                    ESP_LOGE(TAG, "AVI playback failed: %s", esp_err_to_name(result));
                }
                (void)finish_playback(player, true);
            }
        }
    }

    if (take_mutex(player->state_mutex)) {
        player->task_handle = NULL;
        give_mutex(player->state_mutex);
    }
    xEventGroupSetBits(player->event_group, EVENT_DEINIT_DONE);
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 1, 0)
    vTaskDeleteWithCaps(NULL);
#else
    vTaskDelete(NULL);
#endif
}

static void esp_timer_cb(void *arg)
{
    avi_player_t *player = (avi_player_t *)arg;
    xEventGroupSetBits(player->event_group, EVENT_FPS_TIME_UP);
}

esp_err_t avi_player_get_video_buffer(
    avi_player_handle_t handle,
    void **buffer,
    size_t *buffer_size,
    video_frame_info_t *info,
    TickType_t ticks_to_wait
)
{
    avi_player_t *player = (avi_player_t *)handle;
    ESP_RETURN_ON_FALSE(player != NULL, ESP_ERR_INVALID_ARG, TAG, "handle cannot be NULL");
    ESP_RETURN_ON_FALSE(buffer != NULL && *buffer != NULL, ESP_ERR_INVALID_ARG, TAG,
                        "buffer cannot be NULL");
    ESP_RETURN_ON_FALSE(buffer_size != NULL, ESP_ERR_INVALID_ARG, TAG,
                        "buffer_size cannot be NULL");
    ESP_RETURN_ON_FALSE(info != NULL, ESP_ERR_INVALID_ARG, TAG, "info cannot be NULL");

    const EventBits_t bits = xEventGroupWaitBits(
        player->event_group,
        EVENT_VIDEO_BUF_READY,
        pdTRUE,
        pdFALSE,
        ticks_to_wait
    );
    if ((bits & EVENT_VIDEO_BUF_READY) == 0) {
        return ESP_ERR_TIMEOUT;
    }

    if (!take_mutex(player->buffer_mutex)) {
        return ESP_FAIL;
    }
    if (*buffer_size < player->avi_data.str_size) {
        give_mutex(player->buffer_mutex);
        return ESP_ERR_NO_MEM;
    }
    memcpy(*buffer, player->avi_data.pbuffer, player->avi_data.str_size);
    *buffer_size = player->avi_data.str_size;
    info->width = player->avi_data.AVI_file.vids_width;
    info->height = player->avi_data.AVI_file.vids_height;
    info->frame_format = player->avi_data.AVI_file.vids_format;
    give_mutex(player->buffer_mutex);
    return ESP_OK;
}

esp_err_t avi_player_get_audio_buffer(
    avi_player_handle_t handle,
    void **buffer,
    size_t *buffer_size,
    audio_frame_info_t *info,
    TickType_t ticks_to_wait
)
{
    avi_player_t *player = (avi_player_t *)handle;
    ESP_RETURN_ON_FALSE(player != NULL, ESP_ERR_INVALID_ARG, TAG, "handle cannot be NULL");
    ESP_RETURN_ON_FALSE(buffer != NULL && *buffer != NULL, ESP_ERR_INVALID_ARG, TAG,
                        "buffer cannot be NULL");
    ESP_RETURN_ON_FALSE(buffer_size != NULL, ESP_ERR_INVALID_ARG, TAG,
                        "buffer_size cannot be NULL");
    ESP_RETURN_ON_FALSE(info != NULL, ESP_ERR_INVALID_ARG, TAG, "info cannot be NULL");

    const EventBits_t bits = xEventGroupWaitBits(
        player->event_group,
        EVENT_AUDIO_BUF_READY,
        pdTRUE,
        pdFALSE,
        ticks_to_wait
    );
    if ((bits & EVENT_AUDIO_BUF_READY) == 0) {
        return ESP_ERR_TIMEOUT;
    }

    if (!take_mutex(player->buffer_mutex)) {
        return ESP_FAIL;
    }
    if (*buffer_size < player->avi_data.str_size) {
        give_mutex(player->buffer_mutex);
        return ESP_ERR_NO_MEM;
    }
    memcpy(*buffer, player->avi_data.pbuffer, player->avi_data.str_size);
    *buffer_size = player->avi_data.str_size;
    info->channel = player->avi_data.AVI_file.auds_channels;
    info->bits_per_sample = player->avi_data.AVI_file.auds_bits;
    info->sample_rate = player->avi_data.AVI_file.auds_sample_rate;
    info->format = FORMAT_PCM;
    give_mutex(player->buffer_mutex);
    return ESP_OK;
}

esp_err_t avi_player_play_from_memory(
    avi_player_handle_t handle,
    uint8_t *avi_data,
    size_t avi_size
)
{
    avi_player_t *player = (avi_player_t *)handle;
    ESP_RETURN_ON_FALSE(player != NULL && avi_data != NULL, ESP_ERR_INVALID_ARG, TAG,
                        "handle and AVI data cannot be NULL");
    ESP_RETURN_ON_FALSE(avi_size != 0 && avi_size <= UINT32_MAX, ESP_ERR_INVALID_SIZE, TAG,
                        "AVI memory size is invalid");

    if (!take_mutex(player->state_mutex)) {
        return ESP_FAIL;
    }
    if (player->play_active || player->deinit_requested) {
        give_mutex(player->state_mutex);
        return ESP_ERR_INVALID_STATE;
    }
    player->avi_data.mode = PLAY_MEMORY;
    player->avi_data.memory.data = avi_data;
    player->avi_data.memory.size = (uint32_t)avi_size;
    player->avi_data.memory.read_offset = 0;
    player->avi_data.state = AVI_PARSER_HEADER;
    player->play_active = true;
    player->stop_requested = false;
    give_mutex(player->state_mutex);

    xEventGroupSetBits(player->event_group, EVENT_START_PLAY);
    return ESP_OK;
}

esp_err_t avi_player_play_from_file(avi_player_handle_t handle, const char *filename)
{
    avi_player_t *player = (avi_player_t *)handle;
    ESP_RETURN_ON_FALSE(player != NULL && filename != NULL && filename[0] != '\0',
                        ESP_ERR_INVALID_ARG, TAG, "handle and filename cannot be NULL");

    if (!take_mutex(player->state_mutex)) {
        return ESP_FAIL;
    }
    if (player->play_active || player->deinit_requested) {
        give_mutex(player->state_mutex);
        return ESP_ERR_INVALID_STATE;
    }

    FILE *file = fopen(filename, "rb");
    if (file == NULL) {
        give_mutex(player->state_mutex);
        ESP_LOGE(TAG, "Cannot open %s", filename);
        return ESP_FAIL;
    }

    player->avi_data.mode = PLAY_FILE;
    player->avi_data.file.avi_file = file;
    player->avi_data.state = AVI_PARSER_HEADER;
    player->play_active = true;
    player->stop_requested = false;
    give_mutex(player->state_mutex);

    xEventGroupSetBits(player->event_group, EVENT_START_PLAY);
    return ESP_OK;
}

esp_err_t avi_player_play_stop(avi_player_handle_t handle)
{
    avi_player_t *player = (avi_player_t *)handle;
    ESP_RETURN_ON_FALSE(player != NULL, ESP_ERR_INVALID_ARG, TAG, "handle cannot be NULL");

    if (!take_mutex(player->state_mutex)) {
        return ESP_FAIL;
    }
    if (!player->play_active || player->deinit_requested) {
        give_mutex(player->state_mutex);
        return ESP_ERR_INVALID_STATE;
    }
    player->stop_requested = true;
    give_mutex(player->state_mutex);

    // play_active is set before START is queued, so START followed immediately
    // by STOP is valid. The worker gives STOP precedence when both bits arrive.
    xEventGroupSetBits(player->event_group, EVENT_STOP_PLAY);
    return ESP_OK;
}

esp_err_t avi_player_init(avi_player_config_t config, avi_player_handle_t *handle)
{
    ESP_RETURN_ON_FALSE(handle != NULL, ESP_ERR_INVALID_ARG, TAG, "handle cannot be NULL");
    *handle = NULL;
    ESP_LOGI(TAG, "AVI Player Version: %d.%d.%d-safe", AVI_PLAYER_VER_MAJOR,
             AVI_PLAYER_VER_MINOR, AVI_PLAYER_VER_PATCH);

    avi_player_t *player = (avi_player_t *)calloc(1, sizeof(*player));
    ESP_RETURN_ON_FALSE(player != NULL, ESP_ERR_NO_MEM, TAG, "Cannot allocate player");
    player->config = config;
    if (player->config.buffer_size == 0) {
        player->config.buffer_size = 20 * 1024;
    }
    if (player->config.priority == 0) {
        player->config.priority = 5;
    }
    if (player->config.stack_size == 0) {
        player->config.stack_size = 4096;
    }

    esp_err_t result = ESP_ERR_NO_MEM;
    player->avi_data.pbuffer = (uint8_t *)malloc(player->config.buffer_size);
    if (player->avi_data.pbuffer == NULL) {
        goto fail;
    }
    player->state_mutex = xSemaphoreCreateMutex();
    player->buffer_mutex = xSemaphoreCreateMutex();
    player->event_group = xEventGroupCreate();
    if (player->state_mutex == NULL || player->buffer_mutex == NULL ||
        player->event_group == NULL) {
        goto fail;
    }

    const esp_timer_create_args_t timer_args = {
        .callback = esp_timer_cb,
        .arg = player,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "avi_player_timer",
    };
    result = esp_timer_create(&timer_args, &player->timer_handle);
    if (result != ESP_OK) {
        goto fail;
    }

    BaseType_t task_result = pdFAIL;
#if ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(5, 1, 0)
    const BaseType_t stack_caps = player->config.stack_in_psram
                                      ? MALLOC_CAP_SPIRAM
                                      : MALLOC_CAP_INTERNAL;
    task_result = xTaskCreatePinnedToCoreWithCaps(
        avi_player_task,
        "avi_player",
        player->config.stack_size,
        player,
        player->config.priority,
        &player->task_handle,
        player->config.coreID,
        stack_caps
    );
#else
    task_result = xTaskCreatePinnedToCore(
        avi_player_task,
        "avi_player",
        player->config.stack_size,
        player,
        player->config.priority,
        &player->task_handle,
        player->config.coreID
    );
#endif
    if (task_result != pdPASS) {
        result = ESP_ERR_NO_MEM;
        goto fail;
    }

    *handle = player;
    return ESP_OK;

fail:
    if (player->timer_handle != NULL) {
        (void)esp_timer_delete(player->timer_handle);
    }
    if (player->event_group != NULL) {
        vEventGroupDelete(player->event_group);
    }
    if (player->buffer_mutex != NULL) {
        vSemaphoreDelete(player->buffer_mutex);
    }
    if (player->state_mutex != NULL) {
        vSemaphoreDelete(player->state_mutex);
    }
    free(player->avi_data.pbuffer);
    free(player);
    return result;
}

esp_err_t avi_player_deinit(avi_player_handle_t handle)
{
    avi_player_t *player = (avi_player_t *)handle;
    ESP_RETURN_ON_FALSE(player != NULL, ESP_ERR_INVALID_ARG, TAG, "handle cannot be NULL");

    if (!take_mutex(player->state_mutex)) {
        return ESP_FAIL;
    }
    if (player->task_handle == xTaskGetCurrentTaskHandle()) {
        give_mutex(player->state_mutex);
        ESP_LOGE(TAG, "Cannot deinitialize AVI player from its callback task");
        return ESP_ERR_INVALID_STATE;
    }
    player->deinit_requested = true;
    give_mutex(player->state_mutex);

    xEventGroupSetBits(player->event_group, EVENT_DEINIT);
    // Storage-owning callers release their mount lease as soon as deinit
    // returns. Wait without a timeout so the task must close FILE first.
    const EventBits_t bits = xEventGroupWaitBits(
        player->event_group,
        EVENT_DEINIT_DONE,
        pdFALSE,
        pdTRUE,
        portMAX_DELAY
    );
    if ((bits & EVENT_DEINIT_DONE) == 0) {
        return ESP_FAIL;
    }

    if (player->timer_handle != NULL) {
        (void)stop_timer(player);
        const esp_err_t timer_result = esp_timer_delete(player->timer_handle);
        if (timer_result != ESP_OK) {
            ESP_LOGE(TAG, "AVI timer delete failed: %s", esp_err_to_name(timer_result));
            return timer_result;
        }
        player->timer_handle = NULL;
    }

    // The worker has exited and its FILE has been closed. It is now safe to
    // release every internal resource and let the caller release the SD lease.
    free(player->avi_data.pbuffer);
    player->avi_data.pbuffer = NULL;
    vEventGroupDelete(player->event_group);
    player->event_group = NULL;
    vSemaphoreDelete(player->buffer_mutex);
    player->buffer_mutex = NULL;
    vSemaphoreDelete(player->state_mutex);
    player->state_mutex = NULL;
    free(player);
    return ESP_OK;
}
