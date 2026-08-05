/*
 * SPDX-FileCopyrightText: 2024 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef __AVIFILE_H
#define __AVIFILE_H

#include <stdint.h>

#include "avi_def.h"
#include "avi_player.h"

#define RIFF_ID 0x46464952U
#define AVI_ID  0x20495641U
#define LIST_ID 0x5453494cU
#define HDRL_ID 0x6c726468U
#define AVIH_ID 0x68697661U
#define STRL_ID 0x6c727473U
#define STRH_ID 0x68727473U
#define STRF_ID 0x66727473U
#define MOVI_ID 0x69766f6dU
#define MJPG_ID 0x47504a4dU
#define H264_ID 0x34363248U
#define VIDS_ID 0x73646976U
#define AUDS_ID 0x73647561U

#define DB_ID 0x62640000U
#define DC_ID 0x63640000U
#define WB_ID 0x62770000U
#define PC_ID 0x63700000U

typedef struct {
    uint32_t RIFFchunksize;
    uint32_t LISTchunksize;
    uint32_t avihsize;
    uint32_t strlsize;
    uint32_t strhsize;

    uint32_t movi_start;
    uint32_t movi_size;

    uint16_t vids_fps;
    uint16_t vids_width;
    uint16_t vids_height;
    video_frame_format vids_format;

    uint16_t auds_channels;
    uint16_t auds_sample_rate;
    uint16_t auds_bits;
} avi_typedef;

int avi_parser(avi_typedef *avi_file, const uint8_t *buffer, uint32_t length);

#endif
