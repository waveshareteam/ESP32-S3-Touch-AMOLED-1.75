/*
 * SPDX-FileCopyrightText: 2023-2025 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "lvgl.h"
#include "esp_brookesia.hpp"
#ifdef ESP_UTILS_LOG_TAG
#   undef ESP_UTILS_LOG_TAG
#endif
#define ESP_UTILS_LOG_TAG "BS:Squareline"
#include "esp_lib_utils.h"
#include "ui/ui.h"
#include "esp_brookesia_app_squareline_demo.hpp"

#define APP_NAME "Squareline"

using namespace std;
using namespace esp_brookesia::gui;
using namespace esp_brookesia::systems;

LV_IMG_DECLARE(esp_brookesia_app_icon_launcher_squareline_112_112);

namespace esp_brookesia::apps {

static bool isRoundSquarelineScreen(void)
{
    if (ui_screen_splash == nullptr) {
        return false;
    }

    lv_obj_update_layout(ui_screen_splash);
    const int32_t width = lv_obj_get_width(ui_screen_splash);
    const int32_t height = lv_obj_get_height(ui_screen_splash);
    const int32_t delta = width - height;
    return width >= 300 && height >= 300 && delta >= -8 && delta <= width / 4;
}

static void adaptSquarelineUiToRoundScreen(void)
{
    if (!isRoundSquarelineScreen()) {
        return;
    }

    const int32_t screen_width = lv_obj_get_width(ui_screen_splash);
    const int32_t screen_height = lv_obj_get_height(ui_screen_splash);
    const int32_t safe_width = screen_width * 70 / 100;

    // These two clickable images were anchored in the lower physical corners.
    // Preserve their vertical position while bringing both toward the center.
    if (ui_music_player_image_backward != nullptr) {
        lv_obj_set_align(ui_music_player_image_backward, LV_ALIGN_BOTTOM_MID);
        lv_obj_set_x(ui_music_player_image_backward, -screen_width * 15 / 100);
    }
    if (ui_music_player_image_forward != nullptr) {
        lv_obj_set_align(ui_music_player_image_forward, LV_ALIGN_BOTTOM_MID);
        lv_obj_set_x(ui_music_player_image_forward, screen_width * 15 / 100);
    }

    lv_obj_t *alarm_rows[] = {
        ui_alarm_alarm_comp_alarm_comp,
        ui_alarm_alarm_comp_alarm_comp1,
        ui_alarm_alarm_comp_alarm_comp2,
        ui_alarm_alarm_comp_alarm_comp3,
    };
    static constexpr int32_t alarm_y_percent[] = {13, 31, 49, 68};
    for (size_t i = 0; i < sizeof(alarm_rows) / sizeof(alarm_rows[0]); ++i) {
        if (alarm_rows[i] != nullptr) {
            lv_obj_set_width(alarm_rows[i], safe_width);
            lv_obj_set_align(alarm_rows[i], LV_ALIGN_TOP_MID);
            lv_obj_set_x(alarm_rows[i], 0);
            lv_obj_set_y(alarm_rows[i], alarm_y_percent[i] * screen_height / 100);
        }
    }

    lv_obj_t *chat_rows[] = {ui_chat_panel_c1, ui_chat_panel_c2, ui_chat_panel_c3};
    static constexpr int32_t chat_y_percent[] = {13, 34, 58};
    for (size_t i = 0; i < sizeof(chat_rows) / sizeof(chat_rows[0]); ++i) {
        if (chat_rows[i] != nullptr) {
            lv_obj_set_width(chat_rows[i], safe_width);
            lv_obj_set_align(chat_rows[i], LV_ALIGN_TOP_MID);
            lv_obj_set_x(chat_rows[i], 0);
            lv_obj_set_y(chat_rows[i], chat_y_percent[i] * screen_height / 100);
        }
    }

    if (ui_weather_panel_weather_icons != nullptr) {
        lv_obj_set_width(ui_weather_panel_weather_icons, safe_width);
        lv_obj_set_align(ui_weather_panel_weather_icons, LV_ALIGN_BOTTOM_MID);
        lv_obj_set_x(ui_weather_panel_weather_icons, 0);
    }
}

SquarelineDemo *SquarelineDemo::_instance = nullptr;

SquarelineDemo *SquarelineDemo::requestInstance(bool use_status_bar, bool use_navigation_bar)
{
    if (_instance == nullptr) {
        _instance = new SquarelineDemo(use_status_bar, use_navigation_bar);
    }
    return _instance;
}

SquarelineDemo::SquarelineDemo(bool use_status_bar, bool use_navigation_bar):
    App(APP_NAME, &esp_brookesia_app_icon_launcher_squareline_112_112, false, use_status_bar, use_navigation_bar)
{
}

SquarelineDemo::~SquarelineDemo()
{
}

bool SquarelineDemo::run(void)
{
    ESP_UTILS_LOGD("Run");

    // Create all UI resources here
    phone_app_squareline_ui_init();
    adaptSquarelineUiToRoundScreen();

    return true;
}

bool SquarelineDemo::back(void)
{
    ESP_UTILS_LOGD("Back");

    // If the app needs to exit, call notifyCoreClosed() to notify the core to close the app
    ESP_UTILS_CHECK_FALSE_RETURN(notifyCoreClosed(), false, "Notify core closed failed");

    return true;
}

// bool SquarelineDemo::close(void)
// {
//     ESP_UTILS_LOGD("Close");

//     /* Do some operations here if needed */

//     return true;
// }

// bool SquarelineDemo::init()
// {
//     ESP_UTILS_LOGD("Init");

//     /* Do some initialization here if needed */

//     return true;
// }

// bool SquarelineDemo::deinit()
// {
//     ESP_UTILS_LOGD("Deinit");

//     /* Do some deinitialization here if needed */

//     return true;
// }

// bool SquarelineDemo::pause()
// {
//     ESP_UTILS_LOGD("Pause");

//     /* Do some operations here if needed */

//     return true;
// }

// bool SquarelineDemo::resume()
// {
//     ESP_UTILS_LOGD("Resume");

//     /* Do some operations here if needed */

//     return true;
// }

// bool SquarelineDemo::cleanResource()
// {
//     ESP_UTILS_LOGD("Clean resource");

//     /* Do some cleanup here if needed */

//     return true;
// }

extern "C" {

    /**
     * The following functions are generated by Squareline and records resources before and after creating animations,
     * allowing for automatic cleanup of animation resources when the app exits. This prevents errors that may occur when
     * animations call UI elements that have already been cleaned up.
     *
     */
    void upanim_Animation(lv_obj_t *TargetObject, int delay)
    {
        ui_anim_user_data_t *PropertyAnimation_0_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_0_user_data->target = TargetObject;
        PropertyAnimation_0_user_data->val = -1;
        lv_anim_t PropertyAnimation_0;
        lv_anim_init(&PropertyAnimation_0);
        lv_anim_set_time(&PropertyAnimation_0, 200);
        lv_anim_set_user_data(&PropertyAnimation_0, PropertyAnimation_0_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_0, _ui_anim_callback_set_y);
        lv_anim_set_values(&PropertyAnimation_0, -30, 0);
        lv_anim_set_path_cb(&PropertyAnimation_0, lv_anim_path_ease_out);
        lv_anim_set_delay(&PropertyAnimation_0, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_0, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_0, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_0, 0);
        lv_anim_set_early_apply(&PropertyAnimation_0, false);
        lv_anim_set_get_value_cb(&PropertyAnimation_0, &_ui_anim_callback_get_y);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_0);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

        ui_anim_user_data_t *PropertyAnimation_1_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_1_user_data->target = TargetObject;
        PropertyAnimation_1_user_data->val = -1;
        lv_anim_t PropertyAnimation_1;
        lv_anim_init(&PropertyAnimation_1);
        lv_anim_set_time(&PropertyAnimation_1, 100);
        lv_anim_set_user_data(&PropertyAnimation_1, PropertyAnimation_1_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_1, _ui_anim_callback_set_opacity);
        lv_anim_set_values(&PropertyAnimation_1, 0, 255);
        lv_anim_set_path_cb(&PropertyAnimation_1, lv_anim_path_linear);
        lv_anim_set_delay(&PropertyAnimation_1, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_1, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_1, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_1, 0);
        lv_anim_set_early_apply(&PropertyAnimation_1, true);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_1);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

    }
    void hour_Animation(lv_obj_t *TargetObject, int delay)
    {
        ui_anim_user_data_t *PropertyAnimation_0_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_0_user_data->target = TargetObject;
        PropertyAnimation_0_user_data->val = -1;
        lv_anim_t PropertyAnimation_0;
        lv_anim_init(&PropertyAnimation_0);
        lv_anim_set_time(&PropertyAnimation_0, 1000);
        lv_anim_set_user_data(&PropertyAnimation_0, PropertyAnimation_0_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_0, _ui_anim_callback_set_image_angle);
        lv_anim_set_values(&PropertyAnimation_0, 0, 2800);
        lv_anim_set_path_cb(&PropertyAnimation_0, lv_anim_path_ease_out);
        lv_anim_set_delay(&PropertyAnimation_0, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_0, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_0, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_0, 0);
        lv_anim_set_early_apply(&PropertyAnimation_0, false);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_0);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

        ui_anim_user_data_t *PropertyAnimation_1_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_1_user_data->target = TargetObject;
        PropertyAnimation_1_user_data->val = -1;
        lv_anim_t PropertyAnimation_1;
        lv_anim_init(&PropertyAnimation_1);
        lv_anim_set_time(&PropertyAnimation_1, 300);
        lv_anim_set_user_data(&PropertyAnimation_1, PropertyAnimation_1_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_1, _ui_anim_callback_set_opacity);
        lv_anim_set_values(&PropertyAnimation_1, 0, 255);
        lv_anim_set_path_cb(&PropertyAnimation_1, lv_anim_path_linear);
        lv_anim_set_delay(&PropertyAnimation_1, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_1, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_1, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_1, 0);
        lv_anim_set_early_apply(&PropertyAnimation_1, true);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_1);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

    }
    void min_Animation(lv_obj_t *TargetObject, int delay)
    {
        ui_anim_user_data_t *PropertyAnimation_0_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_0_user_data->target = TargetObject;
        PropertyAnimation_0_user_data->val = -1;
        lv_anim_t PropertyAnimation_0;
        lv_anim_init(&PropertyAnimation_0);
        lv_anim_set_time(&PropertyAnimation_0, 1000);
        lv_anim_set_user_data(&PropertyAnimation_0, PropertyAnimation_0_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_0, _ui_anim_callback_set_image_angle);
        lv_anim_set_values(&PropertyAnimation_0, 0, 2100);
        lv_anim_set_path_cb(&PropertyAnimation_0, lv_anim_path_ease_out);
        lv_anim_set_delay(&PropertyAnimation_0, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_0, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_0, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_0, 0);
        lv_anim_set_early_apply(&PropertyAnimation_0, false);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_0);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

        ui_anim_user_data_t *PropertyAnimation_1_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_1_user_data->target = TargetObject;
        PropertyAnimation_1_user_data->val = -1;
        lv_anim_t PropertyAnimation_1;
        lv_anim_init(&PropertyAnimation_1);
        lv_anim_set_time(&PropertyAnimation_1, 200);
        lv_anim_set_user_data(&PropertyAnimation_1, PropertyAnimation_1_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_1, _ui_anim_callback_set_opacity);
        lv_anim_set_values(&PropertyAnimation_1, 0, 255);
        lv_anim_set_path_cb(&PropertyAnimation_1, lv_anim_path_linear);
        lv_anim_set_delay(&PropertyAnimation_1, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_1, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_1, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_1, 0);
        lv_anim_set_early_apply(&PropertyAnimation_1, true);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_1);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

    }
    void sec_Animation(lv_obj_t *TargetObject, int delay)
    {
        ui_anim_user_data_t *PropertyAnimation_0_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_0_user_data->target = TargetObject;
        PropertyAnimation_0_user_data->val = -1;
        lv_anim_t PropertyAnimation_0;
        lv_anim_init(&PropertyAnimation_0);
        lv_anim_set_time(&PropertyAnimation_0, 60000);
        lv_anim_set_user_data(&PropertyAnimation_0, PropertyAnimation_0_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_0, _ui_anim_callback_set_image_angle);
        lv_anim_set_values(&PropertyAnimation_0, 0, 3600);
        lv_anim_set_path_cb(&PropertyAnimation_0, lv_anim_path_linear);
        lv_anim_set_delay(&PropertyAnimation_0, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_0, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_0, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_0, LV_ANIM_REPEAT_INFINITE);
        lv_anim_set_repeat_delay(&PropertyAnimation_0, 0);
        lv_anim_set_early_apply(&PropertyAnimation_0, false);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_0);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

        ui_anim_user_data_t *PropertyAnimation_1_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_1_user_data->target = TargetObject;
        PropertyAnimation_1_user_data->val = -1;
        lv_anim_t PropertyAnimation_1;
        lv_anim_init(&PropertyAnimation_1);
        lv_anim_set_time(&PropertyAnimation_1, 1000);
        lv_anim_set_user_data(&PropertyAnimation_1, PropertyAnimation_1_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_1, _ui_anim_callback_set_opacity);
        lv_anim_set_values(&PropertyAnimation_1, 0, 255);
        lv_anim_set_path_cb(&PropertyAnimation_1, lv_anim_path_linear);
        lv_anim_set_delay(&PropertyAnimation_1, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_1, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_1, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_1, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_1, 0);
        lv_anim_set_early_apply(&PropertyAnimation_1, true);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_1);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );

    }
    void scrolldot_Animation(lv_obj_t *TargetObject, int delay)
    {
        ui_anim_user_data_t *PropertyAnimation_0_user_data = (ui_anim_user_data_t *)lv_malloc(sizeof(ui_anim_user_data_t));
        PropertyAnimation_0_user_data->target = TargetObject;
        PropertyAnimation_0_user_data->val = -1;
        lv_anim_t PropertyAnimation_0;
        lv_anim_init(&PropertyAnimation_0);
        lv_anim_set_time(&PropertyAnimation_0, 300);
        lv_anim_set_user_data(&PropertyAnimation_0, PropertyAnimation_0_user_data);
        lv_anim_set_custom_exec_cb(&PropertyAnimation_0, _ui_anim_callback_set_y);
        lv_anim_set_values(&PropertyAnimation_0, 30, -8);
        lv_anim_set_path_cb(&PropertyAnimation_0, lv_anim_path_ease_out);
        lv_anim_set_delay(&PropertyAnimation_0, delay + 0);
        lv_anim_set_deleted_cb(&PropertyAnimation_0, _ui_anim_callback_free_user_data);
        lv_anim_set_playback_time(&PropertyAnimation_0, 0);
        lv_anim_set_playback_delay(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_count(&PropertyAnimation_0, 0);
        lv_anim_set_repeat_delay(&PropertyAnimation_0, 0);
        lv_anim_set_early_apply(&PropertyAnimation_0, true);

        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->startRecordResource(), "Start record resource failed"
        );
        lv_anim_start(&PropertyAnimation_0);
        ESP_UTILS_CHECK_FALSE_EXIT(
            SquarelineDemo::requestInstance()->endRecordResource(), "End record resource failed"
        );
    }

} // extern "C"

ESP_UTILS_REGISTER_PLUGIN_WITH_CONSTRUCTOR(systems::base::App, SquarelineDemo, APP_NAME, []()
{
    return std::shared_ptr<SquarelineDemo>(SquarelineDemo::requestInstance(), [](SquarelineDemo * p) {});
})

} // namespace esp_brookesia::apps
