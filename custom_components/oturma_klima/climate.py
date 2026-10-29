"""Oturma Klima (Broadlink IR) Platformu."""
import json
import logging
import os

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

_LOGGER = logging.getLogger(__name__)

HVAC_MAP = {
    "off": HVACMode.OFF,
    "cool": HVACMode.COOL,
    "dry": HVACMode.DRY,
}

REVERSE_HVAC_MAP = {v: k for k, v in HVAC_MAP.items()}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Oturma Klima platform."""
    name = config.get("name", "Oturma Klima")
    unique_id = config.get("unique_id", "oturma_klima_ir")
    remote_entity = config.get("remote_entity")
    code_file = config.get("code_file", "arcelik_klima.json")
    temp_sensor_entity = config.get("temperature_sensor")

    file_path = os.path.join(os.path.dirname(__file__), code_file)

    def load_json():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    data = await hass.async_add_executor_job(load_json)
    async_add_entities(
        [LocalIRClimate(hass, name, unique_id, remote_entity, data, temp_sensor_entity)],
        True,
    )


class LocalIRClimate(ClimateEntity):
    """Representation of an IR Climate entity via Broadlink."""

    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, hass, name, unique_id, remote_entity, data, temp_sensor_entity=None):
        self.hass = hass
        self._name = name
        self._unique_id = unique_id
        self._remote_entity = remote_entity
        self._data = data
        self._temp_sensor_entity = temp_sensor_entity

        self._min_temp = int(data.get("minTemperature", 18))
        self._max_temp = int(data.get("maxTemperature", 30))
        self._target_temp = self._min_temp
        self._hvac_mode = HVACMode.OFF
        self._fan_mode = data.get("fanModes", ["low"])[0]

        self._attr_hvac_modes = [
            HVAC_MAP[m] for m in data.get("operationModes", []) if m in HVAC_MAP
        ]
        if HVACMode.OFF not in self._attr_hvac_modes:
            self._attr_hvac_modes.append(HVACMode.OFF)

        self._attr_fan_modes = data.get("fanModes", ["low", "medium", "high"])
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )

    @property
    def name(self):
        """Return the display name."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._min_temp

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._max_temp

    @property
    def target_temperature_step(self):
        """Return the supported temperature step."""
        return 1

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._target_temp

    @property
    def current_temperature(self):
        """Return current temperature from optional sensor."""
        if self._temp_sensor_entity:
            state = self.hass.states.get(self._temp_sensor_entity)
            if state and state.state not in (None, "unknown", "unavailable"):
                try:
                    return float(state.state)
                except (ValueError, TypeError):
                    pass
        return None

    @property
    def hvac_mode(self):
        """Return current operation mode."""
        return self._hvac_mode

    @property
    def fan_mode(self):
        """Return current fan mode."""
        return self._fan_mode

    async def _send_code(self):
        """Send the IR code through the Broadlink remote."""
        commands = self._data.get("commands", {})

        if self._hvac_mode == HVACMode.OFF:
            code = commands.get("off")
        else:
            json_mode = REVERSE_HVAC_MAP.get(self._hvac_mode)
            temp_str = str(int(self._target_temp))
            mode_data = commands.get(json_mode, {})
            fan_data = mode_data.get(self._fan_mode, {})
            code = fan_data.get(temp_str)

        if not code:
            _LOGGER.error(
                "Komut bulunamadı: Mod=%s, Fan=%s, Sıcaklık=%s",
                self._hvac_mode,
                self._fan_mode,
                self._target_temp,
            )
            return

        payload = f"b64:{code}" if not code.startswith("b64:") else code

        await self.hass.services.async_call(
            "remote",
            "send_command",
            {"entity_id": self._remote_entity, "command": payload},
            blocking=True,
        )

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        self._hvac_mode = hvac_mode
        await self._send_code()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is not None:
            self._target_temp = max(self._min_temp, min(self._max_temp, round(temp)))
            if self._hvac_mode != HVACMode.OFF:
                await self._send_code()
            self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._fan_mode = fan_mode
        if self._hvac_mode != HVACMode.OFF:
            await self._send_code()
        self.async_write_ha_state()

    async def async_turn_on(self):
        """Turn on the entity."""
        if HVACMode.COOL in self._attr_hvac_modes:
            await self.async_set_hvac_mode(HVACMode.COOL)
        else:
            await self.async_set_hvac_mode(self._attr_hvac_modes[0])

    async def async_turn_off(self):
        """Turn off the entity."""
        await self.async_set_hvac_mode(HVACMode.OFF)
