# Camper Weather – Installation

## Requirements

- Home Assistant 2026.10.4 or newer recommended
- HACS or a manual custom integration installation
- Internet access for the configured weather, warning, map and radar providers

## HACS

The request to add Camper Weather to the official [HACS default repository](https://github.com/hacs/default/pull/12942) is open, but it has not yet been approved by HACS maintainers.

Until it is accepted:

1. Open HACS and choose **Integrations → ⋮ → Custom repositories**.
2. Add `balronu/ha-camper-weather` with category **Integration**.
3. Install the stable version `v0.1.3`.
4. Let Home Assistant load the integration.
5. Go to **Settings → Devices & services → Add integration** and select `Camper Weather`.

After the official catalog entry is accepted, the integration can be found through the normal HACS search. No duplicate submission is being created.

## Configuration

Set a name, choose Open-Meteo or the configured provider, and select a tracker, Home Zone or fixed coordinates. MET Norway, DWD and RainViewer can be enabled as needed. The standard configuration does not require a paid API key; provider terms still apply.

## Add the card

Use the Lovelace card picker to select **Camper Weather**. When several entries exist, set `entry_id`:

```yaml
type: custom:camper-weather-card
entry_id: YOUR_CONFIG_ENTRY_ID
```

The integration registers its JavaScript through Home Assistant automatically. A manual dashboard resource is not required.

## Verify

Open the card, choose a location and inspect the **Providers** tab. For troubleshooting see the [English user guide](USER_GUIDE_EN.md) and [provider/API notes](provider-api-keys.md).
