#include <assert.h>
#include <stdatomic.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "avi_player.h"
#include "avifile.h"
#include "host_runtime.h"

static atomic_int s_end_count;
static atomic_int s_video_count;
static atomic_int s_audio_count;

static void put_le16(uint8_t *buffer, size_t offset, uint16_t value)
{
    buffer[offset] = (uint8_t)value;
    buffer[offset + 1] = (uint8_t)(value >> 8);
}

static void put_le32(uint8_t *buffer, size_t offset, uint32_t value)
{
    buffer[offset] = (uint8_t)value;
    buffer[offset + 1] = (uint8_t)(value >> 8);
    buffer[offset + 2] = (uint8_t)(value >> 16);
    buffer[offset + 3] = (uint8_t)(value >> 24);
}

static void put_fourcc(uint8_t *buffer, size_t offset, const char value[4])
{
    memcpy(buffer + offset, value, 4);
}

static size_t make_test_avi(uint8_t *buffer, size_t capacity)
{
    assert(capacity >= 236);
    memset(buffer, 0, capacity);

    put_fourcc(buffer, 0, "RIFF");
    put_le32(buffer, 4, 228);
    put_fourcc(buffer, 8, "AVI ");

    put_fourcc(buffer, 12, "LIST");
    put_le32(buffer, 16, 192);
    put_fourcc(buffer, 20, "hdrl");

    put_fourcc(buffer, 24, "avih");
    put_le32(buffer, 28, 56);
    put_le32(buffer, 56, 1);

    put_fourcc(buffer, 88, "LIST");
    put_le32(buffer, 92, 116);
    put_fourcc(buffer, 96, "strl");

    put_fourcc(buffer, 100, "strh");
    put_le32(buffer, 104, 56);
    put_fourcc(buffer, 108, "vids");
    put_fourcc(buffer, 112, "MJPG");
    put_le32(buffer, 128, 1);
    put_le32(buffer, 132, 30);

    put_fourcc(buffer, 164, "strf");
    put_le32(buffer, 168, 40);
    put_le32(buffer, 176, 466);
    put_le32(buffer, 180, 466);
    put_le16(buffer, 184, 1);
    put_le16(buffer, 186, 24);
    put_fourcc(buffer, 188, "MJPG");

    put_fourcc(buffer, 212, "LIST");
    put_le32(buffer, 216, 16);
    put_fourcc(buffer, 220, "movi");
    put_fourcc(buffer, 224, "00dc");
    put_le32(buffer, 228, 4);
    buffer[232] = 0xff;
    buffer[233] = 0xd8;
    buffer[234] = 0xff;
    buffer[235] = 0xd9;
    return 236;
}

static void write_test_file(const char *path)
{
    uint8_t avi[236];
    const size_t size = make_test_avi(avi, sizeof(avi));
    FILE *file = fopen(path, "wb");
    assert(file != NULL);
    assert(fwrite(avi, 1, size, file) == size);
    assert(fclose(file) == 0);
}

static void video_callback(frame_data_t *data, void *argument)
{
    (void)argument;
    assert(data != NULL);
    assert(data->type == FRAME_TYPE_VIDEO);
    assert(data->data_bytes == 4);
    assert(data->video_info.width == 466);
    assert(data->video_info.height == 466);
    atomic_fetch_add(&s_video_count, 1);
}

static void end_callback(void *argument)
{
    (void)argument;
    atomic_fetch_add(&s_end_count, 1);
}

static void fixture_video_callback(frame_data_t *data, void *argument)
{
    (void)argument;
    assert(data != NULL);
    assert(data->type == FRAME_TYPE_VIDEO);
    assert(data->data != NULL && data->data_bytes > 4);
    assert(data->video_info.width == 320);
    assert(data->video_info.height == 240);
    assert(data->video_info.frame_format == FORMAT_MJEPG);
    atomic_fetch_add(&s_video_count, 1);
}

static void fixture_audio_callback(frame_data_t *data, void *argument)
{
    (void)argument;
    assert(data != NULL);
    assert(data->type == FRAME_TYPE_AUDIO);
    assert(data->data != NULL && data->data_bytes == 9600);
    assert(data->audio_info.sample_rate == 24000);
    assert(data->audio_info.bits_per_sample == 16);
    assert(data->audio_info.channel == 2);
    assert(data->audio_info.format == FORMAT_PCM);
    atomic_fetch_add(&s_audio_count, 1);
}

static bool wait_for_count(atomic_int *value, int expected)
{
    const struct timespec delay = {.tv_sec = 0, .tv_nsec = 1000000L};
    for (int attempt = 0; attempt < 2000; ++attempt) {
        if (atomic_load(value) >= expected) {
            return true;
        }
        nanosleep(&delay, NULL);
    }
    return false;
}

static avi_player_handle_t new_player(size_t buffer_size)
{
    avi_player_handle_t player = NULL;
    const avi_player_config_t config = {
        .buffer_size = buffer_size,
        .video_cb = video_callback,
        .avi_play_end_cb = end_callback,
        .priority = 5,
        .coreID = 0,
        .stack_size = 4096,
    };
    assert(avi_player_init(config, &player) == ESP_OK);
    assert(player != NULL);
    return player;
}

static void reset_counters(void)
{
    host_clear_fread_failure();
    atomic_store(&s_end_count, 0);
    atomic_store(&s_video_count, 0);
    atomic_store(&s_audio_count, 0);
    assert(host_open_file_count() == 0);
}

static void test_media_read_failure_closes_file(void)
{
    const char *path = "avi_media_removed.tmp";
    write_test_file(path);
    reset_counters();

    avi_player_handle_t player = new_player(512);
    // Header read succeeds, then the first frame read behaves like removed
    // media/EOF. Playback must fail closed before deinit releases storage.
    host_fail_fread_after(1);
    assert(avi_player_play_from_file(player, path) == ESP_OK);
    assert(wait_for_count(&s_end_count, 1));
    assert(atomic_load(&s_video_count) == 0);
    assert(host_open_file_count() == 0);
    assert(avi_player_deinit(player) == ESP_OK);
    assert(host_open_file_count() == 0);
    host_clear_fread_failure();
    assert(remove(path) == 0);
}

static void test_start_then_immediate_stop(void)
{
    const char *path = "avi_immediate_stop.tmp";
    write_test_file(path);
    reset_counters();

    avi_player_handle_t player = new_player(512);
    assert(avi_player_play_from_file(player, path) == ESP_OK);
    assert(avi_player_play_stop(player) == ESP_OK);
    assert(wait_for_count(&s_end_count, 1));
    assert(host_open_file_count() == 0);
    assert(avi_player_deinit(player) == ESP_OK);
    assert(host_open_file_count() == 0);
    assert(remove(path) == 0);
}

static void test_natural_end_then_deinit(void)
{
    const char *path = "avi_natural_end.tmp";
    write_test_file(path);
    reset_counters();

    avi_player_handle_t player = new_player(512);
    assert(avi_player_play_from_file(player, path) == ESP_OK);
    assert(wait_for_count(&s_end_count, 1));
    assert(atomic_load(&s_video_count) == 1);
    assert(host_open_file_count() == 0);
    assert(avi_player_deinit(player) == ESP_OK);
    assert(host_open_file_count() == 0);
    assert(remove(path) == 0);
}

static void test_pending_stop_then_deinit(void)
{
    const char *path = "avi_stop_deinit.tmp";
    write_test_file(path);
    reset_counters();

    avi_player_handle_t player = new_player(512);
    assert(avi_player_play_from_file(player, path) == ESP_OK);
    assert(avi_player_play_stop(player) == ESP_OK);
    assert(avi_player_deinit(player) == ESP_OK);
    assert(atomic_load(&s_end_count) == 1);
    assert(host_open_file_count() == 0);
    assert(remove(path) == 0);
}

static void test_external_sd_fixture_header(const char *path)
{
    assert(path != NULL);
    FILE *file = fopen(path, "rb");
    assert(file != NULL);

    const size_t header_capacity = 512U * 1024U;
    uint8_t *header = malloc(header_capacity);
    assert(header != NULL);
    const size_t bytes_read = fread(header, 1, header_capacity, file);
    assert(bytes_read > 0 && bytes_read <= UINT32_MAX);
    assert(fclose(file) == 0);

    avi_typedef avi = {0};
    assert(avi_parser(&avi, header, (uint32_t)bytes_read) == 0);
    free(header);

    assert(avi.vids_format == FORMAT_MJEPG);
    assert(avi.vids_width == 320);
    assert(avi.vids_height == 240);
    assert(avi.vids_fps == 10);
    assert(avi.auds_sample_rate == 24000);
    assert(avi.auds_bits == 16);
    assert(avi.auds_channels == 2);
    assert(avi.movi_start > 0);
    assert(avi.movi_size > 0);
}

static void test_external_sd_fixture_playback(const char *path)
{
    reset_counters();
    avi_player_handle_t player = NULL;
    const avi_player_config_t config = {
        .buffer_size = 512U * 1024U,
        .audio_cb = fixture_audio_callback,
        .video_cb = fixture_video_callback,
        .avi_play_end_cb = end_callback,
        .priority = 5,
        .coreID = 0,
        .stack_size = 4096,
    };
    assert(avi_player_init(config, &player) == ESP_OK);
    assert(player != NULL);
    assert(avi_player_play_from_file(player, path) == ESP_OK);
    assert(wait_for_count(&s_audio_count, 1));
    assert(wait_for_count(&s_video_count, 1));
    assert(avi_player_play_stop(player) == ESP_OK);
    assert(wait_for_count(&s_end_count, 1));
    assert(host_open_file_count() == 0);
    assert(avi_player_deinit(player) == ESP_OK);
    assert(host_open_file_count() == 0);
}

static void test_header_larger_than_buffer_fails_closed(void)
{
    const char *path = "avi_small_header_buffer.tmp";
    write_test_file(path);
    reset_counters();

    avi_player_handle_t player = new_player(128);
    assert(avi_player_play_from_file(player, path) == ESP_OK);
    assert(wait_for_count(&s_end_count, 1));
    assert(atomic_load(&s_video_count) == 0);
    assert(host_open_file_count() == 0);
    assert(avi_player_deinit(player) == ESP_OK);
    assert(host_open_file_count() == 0);
    assert(remove(path) == 0);
}

int main(int argc, char **argv)
{
    test_start_then_immediate_stop();
    test_natural_end_then_deinit();
    test_pending_stop_then_deinit();
    test_header_larger_than_buffer_fails_closed();
    test_media_read_failure_closes_file();
    if (argc == 2) {
        test_external_sd_fixture_header(argv[1]);
        test_external_sd_fixture_playback(argv[1]);
    } else {
        assert(argc == 1);
    }
    puts("avi_player host lifecycle tests: PASS");
    return 0;
}
