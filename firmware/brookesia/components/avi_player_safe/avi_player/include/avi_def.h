/*
 * SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef _AVI_DEFINE_H_
#define _AVI_DEFINE_H_

#include <stdint.h>

typedef struct {
    uint32_t FourCC;
    uint32_t size;
} __attribute__((packed)) AVI_CHUNK_HEAD;

typedef struct {
    uint32_t List;
    uint32_t size;
    uint32_t FourCC;
} __attribute__((packed)) AVI_LIST_HEAD;

typedef struct {
    uint32_t FourCC;
    uint32_t size;
    uint32_t us_per_frame;
    uint32_t max_bytes_per_sec;
    uint32_t padding;
    uint32_t flags;
    uint32_t total_frames;
    uint32_t init_frames;
    uint32_t streams;
    uint32_t suggest_buff_size;
    uint32_t width;
    uint32_t height;
    uint32_t reserved[4];
} __attribute__((packed)) AVI_AVIH_CHUNK;

typedef struct {
    int16_t left;
    int16_t top;
    int16_t right;
    int16_t bottom;
} __attribute__((packed)) AVI_RECT_FRAME;

typedef struct {
    uint32_t FourCC;
    uint32_t size;
    uint32_t fourcc_type;
    uint32_t fourcc_codec;
    uint32_t flags;
    uint16_t priority;
    uint16_t language;
    uint32_t init_frames;
    uint32_t scale;
    uint32_t rate;
    uint32_t start;
    uint32_t length;
    uint32_t suggest_buff_size;
    uint32_t quality;
    uint32_t sample_size;
    AVI_RECT_FRAME rcFrame;
} __attribute__((packed)) AVI_STRH_CHUNK;

typedef struct {
    uint32_t FourCC;
    uint32_t size;
    uint32_t size1;
    uint32_t width;
    uint32_t height;
    uint16_t planes;
    uint16_t bitcount;
    uint32_t fourcc_compression;
    uint32_t image_size;
    uint32_t x_pixels_per_meter;
    uint32_t y_pixels_per_meter;
    uint32_t num_colors;
    uint32_t imp_colors;
} __attribute__((packed)) AVI_VIDS_STRF_CHUNK;

typedef struct __attribute__((packed)) {
    uint32_t FourCC;
    uint32_t size;
    uint16_t format_tag;
    uint16_t channels;
    uint32_t samples_per_sec;
    uint32_t avg_bytes_per_sec;
    uint16_t block_align;
    uint32_t bits_per_sample;
} __attribute__((packed)) AVI_AUDS_STRF_CHUNK;

typedef struct {
    AVI_LIST_HEAD strl;
    AVI_STRH_CHUNK strh;
    AVI_VIDS_STRF_CHUNK strf;
} __attribute__((packed)) AVI_STRL_LIST;

typedef struct {
    AVI_LIST_HEAD hdrl;
    AVI_AVIH_CHUNK avih;
    AVI_STRL_LIST strl;
} __attribute__((packed)) AVI_HDRL_LIST;

typedef struct {
    uint32_t FourCC;
    uint32_t flags;
    uint32_t chunkoffset;
    uint32_t chunklength;
} __attribute__((packed)) AVI_IDX1;

#endif
