/*
 * SPDX-FileCopyrightText: 2024-2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "avifile.h"

#include <stdbool.h>
#include <stddef.h>
#include <string.h>

#include "esp_log.h"

static const char *TAG = "avifile";

static bool span_is_valid(size_t offset, size_t size, size_t limit)
{
    return offset <= limit && size <= limit - offset;
}

static uint16_t read_le16(const uint8_t *data)
{
    return (uint16_t)data[0] | ((uint16_t)data[1] << 8);
}

static uint32_t read_le32(const uint8_t *data)
{
    return (uint32_t)data[0] |
           ((uint32_t)data[1] << 8) |
           ((uint32_t)data[2] << 16) |
           ((uint32_t)data[3] << 24);
}

static bool next_chunk_offset(
    size_t offset,
    uint32_t payload_size,
    size_t limit,
    size_t *next_offset
)
{
    const uint64_t padded_size = (uint64_t)payload_size + (payload_size & 1U);
    const uint64_t next = (uint64_t)offset + sizeof(AVI_CHUNK_HEAD) + padded_size;
    if (next > limit || next > SIZE_MAX) {
        return false;
    }
    *next_offset = (size_t)next;
    return true;
}

static int parse_stream_list(
    avi_typedef *avi_file,
    const uint8_t *data,
    size_t length,
    bool *video_found
)
{
    const uint8_t *strh = NULL;
    size_t strh_size = 0;
    const uint8_t *strf = NULL;
    size_t strf_size = 0;

    size_t offset = 0;
    while (span_is_valid(offset, sizeof(AVI_CHUNK_HEAD), length)) {
        const uint32_t id = read_le32(data + offset);
        const uint32_t payload_size = read_le32(data + offset + 4);
        size_t next = 0;
        if (!next_chunk_offset(offset, payload_size, length, &next)) {
            ESP_LOGE(TAG, "Truncated stream-list chunk");
            return -5;
        }

        const uint8_t *payload = data + offset + sizeof(AVI_CHUNK_HEAD);
        if (id == STRH_ID && strh == NULL) {
            strh = payload;
            strh_size = payload_size;
            avi_file->strhsize = payload_size;
        } else if (id == STRF_ID && strf == NULL) {
            strf = payload;
            strf_size = payload_size;
        }
        offset = next;
    }

    if (strh == NULL || strh_size < 56) {
        ESP_LOGE(TAG, "Missing or truncated strh chunk");
        return -5;
    }

    const uint32_t stream_type = read_le32(strh);
    const uint32_t stream_codec = read_le32(strh + 4);
    if (stream_type == VIDS_ID) {
        if (strf == NULL || strf_size < 40) {
            ESP_LOGE(TAG, "Missing or truncated video strf chunk");
            return -5;
        }
        if (stream_codec == MJPG_ID) {
            avi_file->vids_format = FORMAT_MJEPG;
        } else if (stream_codec == H264_ID) {
            avi_file->vids_format = FORMAT_H264;
        } else {
            ESP_LOGE(TAG, "Unsupported video codec 0x%08lx", (unsigned long)stream_codec);
            return -1;
        }

        const uint32_t scale = read_le32(strh + 20);
        const uint32_t rate = read_le32(strh + 24);
        const uint32_t width = read_le32(strf + 4);
        const uint32_t height = read_le32(strf + 8);
        if (scale == 0 || rate < scale || rate / scale > UINT16_MAX ||
            width == 0 || width > UINT16_MAX || height == 0 || height > UINT16_MAX) {
            ESP_LOGE(TAG, "Invalid video stream dimensions or frame rate");
            return -5;
        }

        avi_file->vids_fps = (uint16_t)(rate / scale);
        avi_file->vids_width = (uint16_t)width;
        avi_file->vids_height = (uint16_t)height;
        *video_found = true;
        ESP_LOGI(TAG, "Video stream: %ux%u @ %u fps", avi_file->vids_width,
                 avi_file->vids_height, avi_file->vids_fps);
    } else if (stream_type == AUDS_ID) {
        if (strf == NULL || strf_size < 16) {
            ESP_LOGE(TAG, "Missing or truncated audio strf chunk");
            return -5;
        }
        const uint16_t channels = read_le16(strf + 2);
        const uint32_t sample_rate = read_le32(strf + 4);
        const uint16_t bits = read_le16(strf + 14);
        if (channels == 0 || sample_rate == 0 || sample_rate > UINT16_MAX || bits == 0) {
            ESP_LOGE(TAG, "Invalid audio stream format");
            return -5;
        }
        avi_file->auds_channels = channels;
        avi_file->auds_sample_rate = (uint16_t)sample_rate;
        avi_file->auds_bits = bits;
        ESP_LOGI(TAG, "Audio stream: %u Hz / %u-bit / %u ch",
                 avi_file->auds_sample_rate, avi_file->auds_bits,
                 avi_file->auds_channels);
    }

    return 0;
}

static int parse_header_list(
    avi_typedef *avi_file,
    const uint8_t *data,
    size_t length,
    bool *video_found
)
{
    bool main_header_found = false;
    size_t offset = 0;

    while (span_is_valid(offset, sizeof(AVI_CHUNK_HEAD), length)) {
        const uint32_t id = read_le32(data + offset);
        const uint32_t payload_size = read_le32(data + offset + 4);
        size_t next = 0;
        if (!next_chunk_offset(offset, payload_size, length, &next)) {
            ESP_LOGE(TAG, "Truncated hdrl chunk");
            return -5;
        }

        const uint8_t *payload = data + offset + sizeof(AVI_CHUNK_HEAD);
        if (id == AVIH_ID) {
            if (payload_size < 56) {
                ESP_LOGE(TAG, "Truncated avih chunk");
                return -5;
            }
            avi_file->avihsize = payload_size;
            main_header_found = true;
        } else if (id == LIST_ID) {
            if (payload_size < sizeof(uint32_t)) {
                ESP_LOGE(TAG, "Invalid nested LIST chunk");
                return -5;
            }
            const uint32_t list_type = read_le32(payload);
            if (list_type == STRL_ID) {
                avi_file->strlsize = payload_size;
                const int result = parse_stream_list(
                    avi_file,
                    payload + sizeof(uint32_t),
                    payload_size - sizeof(uint32_t),
                    video_found
                );
                if (result < 0) {
                    return result;
                }
            }
        }
        offset = next;
    }

    if (!main_header_found || !*video_found) {
        ESP_LOGE(TAG, "AVI header has no supported video stream");
        return -5;
    }
    return 0;
}

int avi_parser(avi_typedef *avi_file, const uint8_t *buffer, uint32_t length)
{
    if (avi_file == NULL || buffer == NULL || length < sizeof(AVI_LIST_HEAD)) {
        return -1;
    }
    memset(avi_file, 0, sizeof(*avi_file));

    if (read_le32(buffer) != RIFF_ID || read_le32(buffer + 8) != AVI_ID) {
        return -1;
    }
    avi_file->RIFFchunksize = read_le32(buffer + 4);

    bool header_found = false;
    bool video_found = false;
    bool movi_found = false;
    size_t offset = sizeof(AVI_LIST_HEAD);

    while (span_is_valid(offset, sizeof(AVI_CHUNK_HEAD), length)) {
        const uint32_t id = read_le32(buffer + offset);
        const uint32_t payload_size = read_le32(buffer + offset + 4);
        const size_t payload_offset = offset + sizeof(AVI_CHUNK_HEAD);

        if (id == LIST_ID) {
            if (payload_size < sizeof(uint32_t) ||
                !span_is_valid(payload_offset, sizeof(uint32_t), length)) {
                return -3;
            }
            const uint32_t list_type = read_le32(buffer + payload_offset);
            if (list_type == MOVI_ID) {
                avi_file->movi_start = (uint32_t)(payload_offset + sizeof(uint32_t));
                avi_file->movi_size = payload_size - sizeof(uint32_t);
                movi_found = avi_file->movi_size > 0;
                break;
            }

            size_t next = 0;
            if (!next_chunk_offset(offset, payload_size, length, &next)) {
                return -3;
            }
            if (list_type == HDRL_ID) {
                avi_file->LISTchunksize = payload_size;
                const int result = parse_header_list(
                    avi_file,
                    buffer + payload_offset + sizeof(uint32_t),
                    payload_size - sizeof(uint32_t),
                    &video_found
                );
                if (result < 0) {
                    return result;
                }
                header_found = true;
            }
            offset = next;
            continue;
        }

        size_t next = 0;
        if (!next_chunk_offset(offset, payload_size, length, &next)) {
            return -5;
        }
        offset = next;
    }

    if (!header_found || !video_found) {
        return -5;
    }
    if (!movi_found) {
        ESP_LOGE(TAG, "Could not find a complete movi LIST header");
        return -7;
    }

    ESP_LOGI(TAG, "movi pos:%lu, payload:%lu", (unsigned long)avi_file->movi_start,
             (unsigned long)avi_file->movi_size);
    return 0;
}
