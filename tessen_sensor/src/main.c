#include <stdio.h>
#include <stdint.h>
#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/usb/usb_device.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/settings/settings.h>

// 사용자 정의 헤더
#include "Type.h"
#include "Const.h"
#include "SensorInfo.h"

/* 센서 관련 상수는 SensorInfo.h에서 정의됨 */
// BUILD_ASSERT(DT_NODE_HAS_COMPAT(DT_CHOSEN(zephyr_console), zephyr_cdc_acm_uart), "Console device is not ACM CDC UART device");

/* LED 관련 정의 */
#define LED0_NODE DT_ALIAS(led0)  // Red LED
#define LED1_NODE DT_ALIAS(led1)  // Green LED
#define LED2_NODE DT_ALIAS(led2)  // Blue LED

static const struct gpio_dt_spec led_red = GPIO_DT_SPEC_GET(LED0_NODE, gpios);
static const struct gpio_dt_spec led_green = GPIO_DT_SPEC_GET(LED1_NODE, gpios);
static const struct gpio_dt_spec led_blue = GPIO_DT_SPEC_GET(LED2_NODE, gpios);

static bool led_red_state = false;

/* Flag set from IMU device irq handler */
static struct sensor_trigger data_trigger;
static volatile int irq_from_device;

/* Bluetooth related variables */
#define TESSEN_SERVICE_UUID_VAL BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef0)
static const struct bt_uuid_128 tessen_service_uuid = BT_UUID_INIT_128(TESSEN_SERVICE_UUID_VAL);
static const struct bt_uuid_128 tessen_data_uuid = BT_UUID_INIT_128(BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef1));
static const struct bt_uuid_128 tessen_config_uuid = BT_UUID_INIT_128(BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef2));

#define TESSEN_DATA_MAX_LEN (64)
static uint8 tessen_data[TESSEN_DATA_MAX_LEN];
static uint8 tessen_config[16];
static bool tessen_notify_enabled = false;

/* for debug */
static const char *timeStamp(void);

/* Bluetooth GATT service functions */
static ssize_t read_tessen_data(struct bt_conn *conn, const struct bt_gatt_attr *attr, void *buf, uint16 len, uint16 offset)
{
    return bt_gatt_attr_read(conn, attr, buf, len, offset, tessen_data, sizeof(tessen_data));
}

static ssize_t read_tessen_config(struct bt_conn *conn, const struct bt_gatt_attr *attr, void *buf, uint16_t len, uint16_t offset)
{
    return bt_gatt_attr_read(conn, attr, buf, len, offset, tessen_config, sizeof(tessen_config));
}

static ssize_t write_tessen_config(struct bt_conn *conn, const struct bt_gatt_attr *attr, const void *buf, uint16 len, uint16 offset, uint8_t flags)
{
    if (offset + len > sizeof(tessen_config)) {
        return BT_GATT_ERR(BT_ATT_ERR_INVALID_OFFSET);
    }

    memcpy(tessen_config + offset, buf, len);
    return len;
}

static void tessen_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    tessen_notify_enabled = (value == BT_GATT_CCC_NOTIFY) ? true : false;
    printf("[%s] TESSEN notifications %s (value: 0x%04x)\n", timeStamp(), tessen_notify_enabled ? "enabled" : "disabled", value);
}

/* TESSEN Custom GATT Service */
BT_GATT_SERVICE_DEFINE(tessen_svc,
    BT_GATT_PRIMARY_SERVICE(&tessen_service_uuid),
    BT_GATT_CHARACTERISTIC(&tessen_data_uuid.uuid,
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_READ,
                           read_tessen_data, NULL, NULL),
    BT_GATT_CCC(tessen_ccc_cfg_changed,
                BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
    BT_GATT_CHARACTERISTIC(&tessen_config_uuid.uuid,
                           BT_GATT_CHRC_READ | BT_GATT_CHRC_WRITE,
                           BT_GATT_PERM_READ | BT_GATT_PERM_WRITE,
                           read_tessen_config, write_tessen_config, NULL),
);

/* Bluetooth advertising data */
static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA_BYTES(BT_DATA_UUID16_ALL,
                  BT_UUID_16_ENCODE(BT_UUID_BAS_VAL)),
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, TESSEN_SERVICE_UUID_VAL),
};

static const struct bt_data sd[] = {
    BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME, sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

/* Bluetooth connection callbacks */
static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        printf("Connection failed, err 0x%02x\n", err);
    } else {
        printf("Connected - GATT services ready\n");
        printf("TESSEN service UUID: 12345678-1234-5678-1234-56789abcdef0\n");
        printf("Data characteristic UUID: 12345678-1234-5678-1234-56789abcdef1\n");
        printf("Config characteristic UUID: 12345678-1234-5678-1234-56789abcdef2\n");
    }
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    printf("[%s] Disconnected, reason 0x%02x\n", timeStamp(), reason);
    tessen_notify_enabled = false;  // 연결 끊어지면 알림 비활성화.
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};

/* Bluetooth ready callback */
static void bt_ready(void)
{
    int err;

    printf("[%s] Bluetooth initialized\n", timeStamp());
    printf("[%s] GATT services registered:\n", timeStamp());
    printf("  - TESSEN Service: 12345678-1234-5678-1234-56789abcdef0\n");
    printf("  - Data Characteristic: 12345678-1234-5678-1234-56789abcdef1 (Read+Notify)\n");
    printf("  - Config Characteristic: 12345678-1234-5678-1234-56789abcdef2 (Read+Write)\n");

    if (IS_ENABLED(CONFIG_SETTINGS)) {
        settings_load();
    }

    err = bt_le_adv_start(BT_LE_ADV_CONN_FAST_1, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (err) {
        printf("Advertising failed to start (err %d)\n", err);
        return;
    }

    printf("[%s] Advertising successfully started\n", timeStamp());
}

/* Function to send sensor data via bluetooth */
static void send_sensor_data_bt(struct sensor_value *accel, struct sensor_value *gyro,
                                struct sensor_value *temperature)
{
    if (!tessen_notify_enabled) {
        static int debug_count = 0;
        if (++debug_count % 10 == 0) {  // 10번에 한 번씩 출력 (더 자주)
            printf("[%s] DEBUG: Notifications disabled (count: %d)\n", timeStamp(), debug_count);
        }
        return;
    }

    /* BUG FIX: 1Hz 속도 제한 로직 제거 */

    // Pack sensor data into tessen_data buffer
    // Format: [accel_x][accel_y][accel_z][gyro_x][gyro_y][gyro_z][temp]
    int16_t *data_ptr = (int16_t *)tessen_data;

    data_ptr[0] = (int16_t)(sensor_value_to_double(&accel[0]) * 1000); // accel_x
    data_ptr[1] = (int16_t)(sensor_value_to_double(&accel[1]) * 1000); // accel_y
    data_ptr[2] = (int16_t)(sensor_value_to_double(&accel[2]) * 1000); // accel_z
    data_ptr[3] = (int16_t)(sensor_value_to_double(&gyro[0]) * 1000);  // gyro_x
    data_ptr[4] = (int16_t)(sensor_value_to_double(&gyro[1]) * 1000);  // gyro_y
    data_ptr[5] = (int16_t)(sensor_value_to_double(&gyro[2]) * 1000);  // gyro_z
    data_ptr[6] = (int16_t)(sensor_value_to_double(temperature) * 100); // temp

    // Safe notification - only if connected
    printf("[%s] Sending sensor data via Bluetooth\n", timeStamp());
    int err = bt_gatt_notify(NULL, &tessen_svc.attrs[1], tessen_data, 14);
    printf("[%s] BT notification result: %d\n", timeStamp(), err);

    if (err < 0) {
        // A notification error doesn't necessarily mean the connection is lost.
        // It could be a temporary issue like a full buffer.
        // The 'disconnected' callback is the reliable place to manage connection state.
        printf("[%s] BT notification failed (err: %d)\n", timeStamp(), err);
    }
    else {
        static int success_count = 0;
        success_count++;
        if (success_count % 10 == 0) {  // 10번에 한 번씩 출력 (더 자주)
            printf("[%s] DEBUG: BT notification sent successfully (count: %d)\n", timeStamp(), success_count);
        }
    }
    printf("[%s] Sensor data sent via Bluetooth\n", timeStamp());
}

/* 간단한 I2C 레지스터 읽기 함수 */
static int read_sensor_reg(const struct device *devI2c, uint8_t reg, uint8_t *data)
{
    uint8_t write_buf[1] = {reg};
    struct i2c_msg msgs[2];

    msgs[0].buf = write_buf;
    msgs[0].len = 1;
    msgs[0].flags = I2C_MSG_WRITE | I2C_MSG_STOP;

    msgs[1].buf = data;
    msgs[1].len = 1;
    msgs[1].flags = I2C_MSG_READ | I2C_MSG_STOP;

    return i2c_transfer(devI2c, msgs, 2, LSM6DS_I2C_ADDR);
}

/* I2C 레지스터 쓰기 함수 */
static int write_sensor_reg(const struct device *devI2c, uint8_t reg, uint8_t data)
{
    uint8_t write_buf[2] = {reg, data};
    struct i2c_msg msgs[1];

    msgs[0].buf = write_buf;
    msgs[0].len = 2;
    msgs[0].flags = I2C_MSG_WRITE | I2C_MSG_STOP;

    return i2c_transfer(devI2c, msgs, 1, LSM6DS_I2C_ADDR);
}

/* 센서 활성화 함수 */
static int activate_sensor_directly(const struct device *devI2c)
{
    int rc = 0;
    printf("[%s] === Activating Sensor Directly ===\n", timeStamp());

    /* CTRL1_XL 설정: 가속도계 활성화 (104Hz, ±2g) */
    rc = write_sensor_reg(devI2c, LSM6DSL_REG_CTRL1_XL, LSM6DS_CTRL1_XL_104HZ_2G);

    /* CTRL2_G 설정: 자이로스코프 활성화 (104Hz, ±250dps) */
    rc = write_sensor_reg(devI2c, LSM6DSL_REG_CTRL2_G, LSM6DS_CTRL2_G_104HZ_250DPS);

    /* CTRL3_C 설정: 기본 설정 유지 */
    rc = write_sensor_reg(devI2c, LSM6DSL_REG_CTRL3_C, LSM6DS_CTRL3_C_DEFAULT);

    return 0;
}

/*
 * Get a device structure from a devicetree node from alias
 * "6dof_motion_drdy0".
 */
static const struct device *get_tessen_devSensorice(void)
{
    const struct device *const dev = DEVICE_DT_GET(DT_ALIAS(6dof_motion_drdy0));

    if (!device_is_ready(dev)) {
        printk("\nError: Device \"%s\" is not ready; "
               "check the driver initialization logs for errors.\n",
               dev->name);
        return NULL;
    }

    printk("Found device \"%s\", getting sensor data\n", dev->name);
    return dev;
}

static const char *timeStamp(void)
{
    static char buf[16]; /* ...HH:MM:SS.MMM */
    uint32_t now = k_uptime_get_32();
    unsigned int ms = now % MSEC_PER_SEC;
    unsigned int s;
    unsigned int min;
    unsigned int h;

    now /= MSEC_PER_SEC;
    s = now % 60U;
    now /= 60U;
    min = now % 60U;
    now /= 60U;
    h = now;

    snprintf(buf, sizeof(buf), "%u:%02u:%02u.%03u", h, min, s, ms);
    return buf;
}

static void handle_tessen_sensor_data(const struct device *dev, const struct sensor_trigger *trig)
{
    //printf("IRQ triggered! Type: %d, Channel: %d\n", trig->type, trig->chan);

    if (trig->type == SENSOR_TRIG_DATA_READY) {
        int rc = sensor_sample_fetch_chan(dev, trig->chan);

        if (rc < 0) {
            printf("sample fetch failed: %d, not cancelling trigger.\n", rc);
            //(void)sensor_trigger_set(dev, trig, NULL); // BUG FIX: DO NOT DISABLE IRQ
            return;
        }
        else if (rc == 0) {
            //printf("Sample fetch successful, setting irq flag\n");
            irq_from_device = 1;
        }
    }
}

int32 initUSB()
{
    const struct device *const devConsole = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));
    int32 ret = 0; // 0: success, -1: error, -2: timeout
    uint32 dtr = 0;
    if (usb_enable(NULL)) {
        ret = -1;
    }
    else {
        /* Poll if the DTR flag was set */
        while (!dtr) {
            uart_line_ctrl_get(devConsole, UART_LINE_CTRL_DTR, &dtr);
            /* Give CPU resources to low priority threads. */
            k_sleep(K_MSEC(100));
            if (++dtr > 50) {
                printf("[%s] USB Console initialization timeout\n", timeStamp());
                ret = -2;
                break;
            }
        }
        printf("[%s] USB Console initialized. Starting TESSEN tennis sensor...\n", timeStamp());
    }
    return ret;
}

void initLED()
{
    // Red LED 초기화.
    if (!gpio_is_ready_dt(&led_red)) {
        printf("Red LED device not ready\n");
    }
    else {
        int ret = gpio_pin_configure_dt(&led_red, GPIO_OUTPUT_ACTIVE);
        if (ret < 0) {
            printf("Failed to configure Red LED: %d\n", ret);
        }
        else {
            printf("[%s] Red LED initialized\n", timeStamp());
        }
    }

    // Green LED 초기화.
    if (!gpio_is_ready_dt(&led_green)) {
        printf("Green LED device not ready\n");
    }
    else {
        int ret = gpio_pin_configure_dt(&led_green, GPIO_OUTPUT_ACTIVE);
        if (ret < 0) {
            printf("Failed to configure Green LED: %d\n", ret);
        }
        else {
            printf("[%s] Green LED initialized\n", timeStamp());
        }
    }

    // Blue LED 초기화.
    if (!gpio_is_ready_dt(&led_blue)) {
        printf("Blue LED device not ready\n");
    }
    else {
        int ret = gpio_pin_configure_dt(&led_blue, GPIO_OUTPUT_ACTIVE);
        if (ret < 0) {
            printf("Failed to configure Blue LED: %d\n", ret);
        }
        else {
            printf("[%s] Blue LED initialized\n", timeStamp());
        }
    }
}

int main(void)
{
    uint32 dtr = 0;
    int rc;

    initUSB();
    initLED();

    // initBluetooth();
    rc = bt_enable(NULL);
    if (rc) {
        printf("Bluetooth init failed (err %d)\n", rc);
        return 0;
    }

    bt_ready();

    // init gyro sensor.
    const struct device *devSensor = get_tessen_devSensorice();
    struct sensor_value accel[3];
    struct sensor_value gyro[3];
    struct sensor_value temperature;

    if (devSensor == NULL) {
        printf("Sensor device not found. Exiting...\n");
        return 0;
    }

    k_sleep(K_MSEC(5000));

    /* I2C 디바이스 초기화 및 직접 레지스터 접근 테스트 */
    printf("Initializing I2C device for direct register access...\n");
    const struct device *devI2c = DEVICE_DT_GET(DT_NODELABEL(i2c0));

    activate_sensor_directly(devI2c);


    #if 1
    data_trigger = (struct sensor_trigger) {
        .type = SENSOR_TRIG_DATA_READY,
        .chan = SENSOR_CHAN_ALL,
    };

    if (sensor_trigger_set(devSensor, &data_trigger, handle_tessen_sensor_data) < 0) {
        printf("Cannot configure data trigger!!!\n");
        return 0;
    }
    #endif

    uint32 sampleCount = 0;
    uint32 ledTimer = 0;

    while (1) {
        sampleCount++;

        /* Red LED 깜빡임 (1초마다) */
        ledTimer++;
        if (ledTimer >= 10) {  // 100ms * 10 = 1초
            ledTimer = 0;
            led_red_state = !led_red_state;
            gpio_pin_set_dt(&led_red, led_red_state);
            //printf("Red LED %s\n", led_red_state ? "ON" : "OFF");
        }

        if (irq_from_device) { // irq mode
            sensor_channel_get(devSensor, SENSOR_CHAN_ACCEL_XYZ, accel);
            sensor_channel_get(devSensor, SENSOR_CHAN_GYRO_XYZ, gyro);
            sensor_channel_get(devSensor, SENSOR_CHAN_DIE_TEMP, &temperature);

            printf("[%s] #%d: temp %.2f accel %f %f %f m/s/s gyro %f %f %f rad/s\n",
                timeStamp(), sampleCount, sensor_value_to_double(&temperature),
                sensor_value_to_double(&accel[0]), sensor_value_to_double(&accel[1]),
                sensor_value_to_double(&accel[2]), sensor_value_to_double(&gyro[0]),
                sensor_value_to_double(&gyro[1]), sensor_value_to_double(&gyro[2]));

            // Send sensor data via Bluetooth
            send_sensor_data_bt(accel, gyro, &temperature);

            irq_from_device = 0;
        }

        k_sleep(K_MSEC(SENSOR_POLL_INTERVAL_MS)); /* 센서 폴링 주기 */
    }
    return 0;
}
