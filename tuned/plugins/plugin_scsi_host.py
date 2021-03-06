import errno
import hotplug
from decorators import *
import tuned.logs
import tuned.consts as consts
from tuned.utils.commands import commands
import os
import re

log = tuned.logs.get()

class DiskPlugin(hotplug.Plugin):
	"""
	Plugin for tuning options of SCSI hosts.
	"""

	def __init__(self, *args, **kwargs):
		super(self.__class__, self).__init__(*args, **kwargs)

		self._cmd = commands()

	def _init_devices(self):
		self._devices = set()
		for device in self._hardware_inventory.get_devices("scsi"):
			if self._device_is_supported(device):
				self._devices.add(device.sys_name)

		self._assigned_devices = set()
		self._free_devices = self._devices.copy()

	def _device_is_supported(cls, device):
		return  device.device_type == "scsi_host"

	def _hardware_events_init(self):
		self._hardware_inventory.subscribe(self, "scsi", self._hardware_events_callback)

	def _hardware_events_cleanup(self):
		self._hardware_inventory.unsubscribe(self)

	def _hardware_events_callback(self, event, device):
		if self._device_is_supported(device):
			super(self.__class__, self)._hardware_events_callback(event, device)

	def _added_device_apply_tuning(self, instance, device_name):
		super(self.__class__, self)._added_device_apply_tuning(instance, device_name)

	def _removed_device_unapply_tuning(self, instance, device_name):
		super(self.__class__, self)._removed_device_unapply_tuning(instance, device_name)

	@classmethod
	def _get_config_options(cls):
		return {
			"alpm"               : None,
		}

	def _instance_init(self, instance):
		instance._has_static_tuning = True
		instance._has_dynamic_tuning = False

	def _instance_cleanup(self, instance):
		pass

	def _get_alpm_policy_file(self, device):
		return os.path.join("/sys/class/scsi_host/", str(device), "link_power_management_policy")

	@command_set("alpm", per_device = True)
	def _set_alpm(self, policy, device, sim):
		if policy is None:
			return None
		policy_file = self._get_alpm_policy_file(device)
		if not sim:
			if os.path.exists(policy_file):
				self._cmd.write_to_file(policy_file, policy)
			else:
				log.warn("ALPM control file ('%s') not found, skipping ALPM setting for '%s'" % (policy_file, str(device)))
				return None
		return policy

	@command_get("alpm")
	def _get_alpm(self, device):
		policy_file = self._get_alpm_policy_file(device)
		policy = self._cmd.read_file(policy_file).strip()
		return policy if policy != "" else None
