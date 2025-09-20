<div align="center">
  <h2>CATLINK v2 Integration for Home Assistant</h2>
</div>

<div align="center">
  <img src="https://play-lh.googleusercontent.com/eHPhN_fUDhdxMK4JAvlzjB5Mh-H72crLn2U3Khk37lzolNg2CTDgZXkB5bjPiM3CDqM" alt="CatLINK Logo" width="100">
  <span style="font-size: 50px; margin: 0 20px;">+</span>
  <img src="https://upload.wikimedia.org/wikipedia/en/thumb/4/49/Home_Assistant_logo_%282023%29.svg/2048px-Home_Assistant_logo_%282023%29.svg.png" alt="Home Assistant Logo" width="100">
</div>

<div align="center">
  <h3>Made easy, for 😸 lovers.</h3>
</div>

<br>

<div align="right">
  <span style="margin-right: 10px; font-size: 16px; font-style: italic">Spotted the issue?</span>
  <a href="https://github.com/hasscc/catlink/issues/new?assignees=&labels=bug%2Ctriage&template=bug_report.md&title=%5BBug%5D%3A+" target="_blank" style="text-decoration: none;"><span style="background-color: #f44b42; border: none; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 4px;">Report a Bug</span></a>
</div>

---

### Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Easy way](#easy-way)
  - [Manually](#manually)
  - [Configuration Example](#configuration-example)
- [Supported Devices and Operations](#supported-devices-and-operations)
  - [Scooper SE](#supported-devices-and-operations)
  - [Scooper PRO](#supported-devices-and-operations)
- [How to Configure?](#how-to-configure)
  - [Configuration via Home Assistant UI](#configuration-via-home-assistant-ui)
  - [Adjusting Options and Device Tuning](#adjusting-options-and-device-tuning)
  - [YAML Compatibility](#yaml-compatibility)
  - [API Regions](#api-regions)
- [Services (Optional)](#services-optional)
- [How to contribute?](#how-to-contribute)
- [Disclaimer on Using Logos](#disclaimer-on-using-logos)

The CatLINK custom integration provides seamless support for integrating your CatLINK Scooper and Litterbox devices into Home Assistant. This integration allows you to monitor, control, and automate your CatLINK devices directly from your Home Assistant setup, enhancing the convenience and care of your feline friends.

#### Features:

- **Scooper/Litterbox Device Integration**: Effortlessly connect your CatLINK Scooper and Litterbox devices to Home Assistant, enabling centralized control and monitoring within your smart home environment.

- **Real-Time Status Monitoring**: Track essential metrics such as work status, alarm status, weight, litter weight, cleaning times, and more. All relevant data is available in real-time, ensuring you stay informed about your pet's litterbox usage.

- **Mode Selection**: Choose between different modes of operation (Auto, Manual, Time) to customize the behavior of your CatLINK devices according to your needs and preferences.

- **Advanced Actions**: Perform specific actions such as initiating a clean cycle, pausing the device, or changing the litter bag directly from Home Assistant.

- **Home Assistant UI Configuration & Options**: Set up the integration through a guided config flow, pick the closest CatLINK region, pick your preferred language, and fine-tune update intervals or device parameters later via the integration's Options dialog.

- **Fresh2 Smart Feeder Enhancements**: Fine-tune feeding modes, track bowl balance, and leverage automatic eating-event detection for the latest Fresh2 feeder series directly inside Home Assistant.

- **Pure2 Water Fountain Monitoring**: Keep an eye on water levels, filter life, water quality, and operating modes of Pure2 fountains without leaving your dashboard.

- **Automatic YAML Migration Support**: Existing YAML-based configurations are imported into config entries on startup, so you can keep historical settings while benefiting from the new UI-first experience.

- **Comprehensive Logging**: Access detailed event logs for all activities, including manual and auto-clean events, cat visits with associated cat details, and other device operations. This feature helps you keep track of your pets' habits and the device's performance.

- **Customizable Alerts and Automations**: Set up notifications and automate tasks based on the state of your CatLINK devices. For example, receive alerts when the litterbox is full or automatically start a cleaning cycle during quiet times.

- **Entity Attributes**: The integration exposes various attributes related to your CatLINK devices, such as litter weight, total and manual clean times, alarm status, and more, allowing for detailed customization and automation.

---

# Installation:

### Easy way
[![HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?category=integration&owner=hasscc&repository=catlink)

### Manually

#### Method 1: Manually installation via Samba / SFTP
> Download and copy `custom_components/catlink` folder to `custom_components` folder in your HomeAssistant config folder

#### Method 2: Onkey shell via SSH / Terminal & SSH add-on
```shell
wget -O - https://get.hacs.vip | DOMAIN=catlink REPO_PATH=hasscc/catlink ARCHIVE_TAG=main bash -
```

#### Method 3: shell_command service
1. Copy this code to file `configuration.yaml`
    ```yaml
    shell_command:
      update_catlink: |-
        wget -O - https://get.hacs.vip | DOMAIN=catlink REPO_PATH=hasscc/catlink ARCHIVE_TAG=main bash -
    ```
2. Restart HA core
3. Call this [`service: shell_command.update_catlink`](https://my.home-assistant.io/redirect/developer_call_service/?service=shell_command.update_catlink) in Developer Tools
2. Restart HA core again

### Configuration Example:

```yaml
catlink:
  phone: "xxxxxx"
  password: "xxxxxx"
  phone_iac: 86 # Default
  api_base: "https://app-usa.catlinks.cn/api/"
  scan_interval: "00:00:10"
  language: "en_GB"

  # Multiple accounts (Optional)
  accounts:
    - username: 18866660001
      password: password1
    - username: 18866660002
      password: password2
```

## Supported Devices and Operations

<div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px;">

  <div style="text-align: center; width: 45%;">
    <h3><a href="https://www.catlinkus.com/products/catlink-smart-litter-box-scooper-se">Scooper SE</a></h3>
    <img src="https://www.catlinkus.com/cdn/shop/files/CATLINK-Lite-01_757acadb-ebb8-4469-88c6-3ca3dd820706_610x610_crop_center.jpg?v=1691003577" alt="Scooper SE" width="150">
    <h4>Operations</h4>
    <ul style="text-align: left;">
      <li>Changing Operation Mode (Auto, Manual, Time)</li>
      <li>Actions (Cleaning, Pause, Change Garbage Bag)</li>
      <li>Wastebin Full flag</li>
      <li>Litter weight measurement</li>
      <li>Litter days left</li>
      <li>Deodorant replacement countdown in days</li>
      <li>Occupacy flag</li>
      <li>Cleaning count</li>
      <li>Knob status</li>
      <li>Garbage Tobe status</li>
      <li>Online status</li>
      <li>Logs & Errors</li>
    </ul>
  </div>

  <div style="text-align: center; width: 45%;">
    <h3><a href="https://www.catlinkus.com/products/catlink-self-cleaning-cat-litter-box-pro">Scooper PRO</a></h3>
    <img src="https://www.catlinkus.com/cdn/shop/files/1500-1500_610x610_crop_center.jpg?v=1691705114" alt="Scooper PRO" width="150">
    <h4>Operations</h4>
    <ul style="text-align: left;">
      <li>Changing Operation Mode (Auto, Manual, Time, Empty)</li>
      <li>Actions (Start, Pause)</li>
      <li>Deodorant replacement countdown in days</li>
      <li>Litter days left</li>
      <li>Litter weight measurement</li>
      <li>Occupacy flag</li>
      <li>Cleaning count</li>
      <li>Temperature (Celsius)</li>
      <li>Humidity</li>
      <li>Online status</li>
      <li>Logs & Error</li>
    </ul>
  </div>

  <div style="text-align: center; width: 45%;">
    <h3><a href="https://www.catlinkus.com/products/catlink-ai-feeder-for-only-pet-young">Feeder Young</a></h3>
    <img src="https://cdn.shopify.com/s/files/1/0641/0056/5251/files/3_94db5ca7-eeeb-4f76-bd7a-c35c3a434a48_610x610_crop_center.jpg?v=1718122855" alt="Feeder Young" width="150">
    <h4>Operations</h4>
    <ul style="text-align: left;">
      <li>Feed Button</li>
      <li>Food tray weight</li>
      <li>Online status</li>
      <li>Logs & Error</li>
    </ul>
  </div>

  <div style="text-align: center; width: 45%;">
    <h3><a href="https://www.catlinkus.com/products/catlink-automatic-feeder-fresh-2-standard">Fresh 2 Smart Feeder</a></h3>
    <img src="https://www.catlinkus.com/cdn/shop/files/CATLINK-Automatic-Feeder---Fresh-2-05_3a53fdd2-5879-4f91-a95e-cc93eb5bd589_1220x1220_crop_center.jpg" alt="Fresh 2 Smart Feeder" width="150">
    <h4>Operations</h4>
    <ul style="text-align: left;">
      <li>Changing Operation Mode (Smart Mode, Timing Mode)</li>
      <li>Adjust feeding portions and daily allowances</li>
      <li>Bowl balance, total intake, and daily eating analytics</li>
      <li>Eating status with real-time event detection</li>
      <li>Desiccant countdown and total balance insights</li>
      <li>Connectivity, child lock, indicator light, night mode, and battery status</li>
      <li>Logs & Error</li>
      <li>Timing schedule and error alert switches</li>
    </ul>
  </div>

  <div style="text-align: center; width: 45%;">
    <h3><a href="https://www.catlinkus.com/products/catlink-ultra-filtration-water-fountain-pure-2">Pure 2 Smart Water Fountain</a></h3>
    <img src="https://www.catlinkus.com/cdn/shop/files/Frame_600_1220x1220_crop_center.png" alt="Pure 2 Smart Water Fountain" width="150">
    <h4>Operations</h4>
    <ul style="text-align: left;">
      <li>Selecting Run Modes (Continuous, Smart, Intermittent Spring)</li>
      <li>Water level percentage and descriptive status</li>
      <li>Filter element countdown in days</li>
      <li>Water quality and temperature monitoring</li>
      <li>Fluffy hair filter and pure light status</li>
      <li>UV light, water heater, lock, and connectivity flags</li>
      <li>Logs & Error</li>
    </ul>
  </div>

</div>

### How to Configure?

> ! Recommend sharing devices to another account, because you can keep only one login session, which means that you'll have to re-login to CATLINK each time your HA instance pulls the data.

#### Configuration via Home Assistant UI

1. Navigate to **Settings → Devices & Services → Add Integration** in Home Assistant and search for **CatLink**.
2. Enter your CatLINK account phone number, country/region code, password, and pick the closest CatLINK server to authenticate.
3. Choose how often the integration should refresh data, set the language used for entity names, and decide whether to tweak device-specific parameters during setup.
4. (Optional) Provide litter box empty weight, litter weight sampling, and Fresh2 eating-detection thresholds to tailor entity readings before confirming the flow.
5. Review the summary screen and submit to create the config entry. Your CatLINK devices will be added to the device registry with entities grouped per physical device.

#### Adjusting Options and Device Tuning

- Open the CatLink integration tile in **Settings → Devices & Services**, click **Configure**, and adjust account credentials, server region, update interval, interface language, or device tuning without removing the integration.
- Device tuning covers litter box calibration along with Fresh2 feeder stability duration, minimum eating amount, and spike thresholds so you can refine automatic eating detection as habits change.

#### YAML Compatibility

- Existing YAML configuration remains supported, and any CatLink accounts defined there will automatically import into config entries on startup. The YAML `devices` section can still be used for per-device overrides alongside the UI options flow.

```yaml
# configuration.yaml

catlink:
  # Single account
  phone: xxxxxxxxx # Username of Catlink APP (without country code)
  password: xxxxxxxxxx # Password
  phone_iac: 86 # Optional, International access code, default is 86 (China)
  api_base: # Optional, default is China server: https://app.catlinks.cn/api/ (see API Regions)
  scan_interval: # Optional, default is 00:01:00
  language: "en_GB"

  devices: # Optional
    - name: "Scooper C1" # Optional
      mac: "AABBCCDDEE" # Optional
      empty_weight: 3.0 # (Optional) Empty litterbox weight defaults to 0.0
      max_samples_litter: 24 # (Optional) Number of samples to determinate whether cat is inside

    - name: "Fresh2 Feeder" # Optional - customize Fresh 2 eating detection
      mac: "FFEEDDCCBB" # Optional
      stable_duration: 60 # (Optional) Seconds of steady weight before considered stable
      min_eating_amount: 2 # (Optional) Minimum grams consumed to register an event
      spike_threshold: 100 # (Optional) Weight spike in grams that indicates a cat at the bowl


  # Multiple accounts
  accounts:
    - username: 18866660001
      password: password1
    - username: 18866660002
      password: password2
```

#### API Regions

> To verify your region, please navigate to `Me` > `Settings` > `Server Nodes`

<p style="font-size: 12px; font-style:italic"> Please precise your location, as number of features might depend on it. </p>

<table style="width: 100%; border-collapse: collapse; text-align: left;">

  <thead>
    <tr>
      <th style="padding: 8px 10px; border-bottom: 1px solid #ddd; font-weight: bold;">Region</th>
      <th style="padding: 8px 10px; border-bottom: 1px solid #ddd; font-weight: bold;">API Base</th>
    </tr>
  </thead>

  <tbody>
    <tr>
      <td style="padding: 8px 10px;"><span style="font-size: 20px;">🌎</span> Global/Recomended</td>
      <td style="padding: 8px 10px;"><a href="https://app.catlinks.cn/api/" target="_blank" style="color: #0066cc; text-decoration: none;">https://app.catlinks.cn/api/</a></td>
    </tr>
    <tr>
      <td style="padding: 8px 10px;"><span style="font-size: 20px;">🇨🇳</span> Mainland China (Sh)</td>
      <td style="padding: 8px 10px;"><a href="https://app-sh.catlinks.cn/api/" target="_blank" style="color: #0066cc; text-decoration: none;">https://app-sh.catlinks.cn/api/</a></td>
    </tr>
    <tr>
      <td style="padding: 8px 10px;"><span style="font-size: 20px;">🇺🇸</span> Euroamerica</td>
      <td style="padding: 8px 10px;"><a href="https://app-usa.catlinks.cn/api/" target="_blank" style="color: #0066cc; text-decoration: none;">https://app-usa.catlinks.cn/api/</a></td>
    </tr>
    <tr>
      <td style="padding: 8px 10px;"><span style="font-size: 20px;">🇸🇬</span> Singapore</td>
      <td style="padding: 8px 10px;"><a href="https://app.catlinks.cn/api/" target="_blank" style="color: #0066cc; text-decoration: none;">https://app-sgp.catlinks.cn/api/</a></td>
    </tr>
  </tbody>

</table>

## Services (Optional)

#### Request API

```yaml
service: catlink.request_api
target:
  entity_id: sensor.scooper_xxxxxx_state # Any sensor entity in the account
data:
  api: /token/device/union/list/sorted
  params:
    key: val
  method: GET # Optional (GET, POST, POST_GET)
  throw: true # Optional, set to false to suppress integration exceptions
```

### How to contribute?

Please visit [CONTRIBUTE](/CONTRIBUTE.md), and be aware of [this](/CODE_OF_CONDUCT.md).

---

### Disclaimer on Using Logos

<p style="font-size: 12px; color: gray;">
  <strong>Disclaimer on Using Logos:</strong> Please note that the logos used in this documentation, including the CatLINK and Home Assistant logos, are the property of their respective owners.
  <br><br>
  <em>Trademark Acknowledgment:</em> The CatLINK and Home Assistant logos are trademarks of their respective companies. This documentation uses these logos solely for informational and illustrative purposes. No endorsement by or affiliation with the trademark holders is implied.
  <br><br>
  <em>Usage Restrictions:</em> Ensure that you have the appropriate permissions or licenses to use these logos in your own materials. Unauthorized use of logos can result in trademark infringement or other legal issues.
  <br><br>
  <em>Modifications:</em> If you modify or resize the logos for use in your projects, ensure that the integrity of the logos is maintained and that they are not used in a misleading or inappropriate manner.
  <br><br>
  By using these logos in your documentation or materials, you acknowledge and agree to comply with all applicable trademark laws and the usage guidelines set by the respective trademark holders.
</p>
