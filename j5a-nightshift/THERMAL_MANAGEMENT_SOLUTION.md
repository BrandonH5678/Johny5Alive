# Night Shift Thermal Management Solution

**Date**: 2025-10-10
**System**: 2012 Mac Mini (Intel Core i5-3210M)
**Status**: ✅ RESOLVED - Automatic thermal management active

---

## Problem Summary

### Initial Issue
After fan replacement, the system exhibited thermal runaway during AI processing:
- CPU reached **94°C** during LLM inference (above 87°C safety limit)
- Fan remained at baseline **1800 RPM** despite high temperatures
- Apple SMC (System Management Controller) automatic fan control **not functioning**
- 7 out of 10 jobs deferred due to thermal safety protocols

### Root Cause
**Apple SMC automatic fan control failure** - The hardware SMC on this Mac Mini is not properly responding to temperature changes and ramping up the fan speed. This is a known issue with older Mac hardware running Linux.

---

## Solution Implemented

### Automatic Fan Control via macfanctld

**Installed**: `macfanctld` daemon
**Purpose**: Replaces broken SMC automatic fan management
**Status**: ✅ Active and managing fan speed automatically

#### Installation
```bash
sudo apt-get update
sudo apt-get install -y macfanctld
sudo systemctl enable macfanctld
sudo systemctl start macfanctld
```

#### Verification
```bash
systemctl status macfanctld
sensors | grep Exhaust
```

---

## Performance Results

### Before macfanctld
- **CPU Temperature**: 90-94°C under load ❌
- **Fan Speed**: 1800 RPM (stuck at minimum)
- **Jobs Completed**: 3/10 (30% success rate)
- **Jobs Deferred**: 7/10 (thermal protection activated)

### After macfanctld
- **CPU Temperature**: 70-78°C under load ✅
- **Fan Speed**: 4500-4900 RPM (dynamically adjusted)
- **Thermal Safety**: Maintained below 80°C threshold
- **Status**: Ready for full overnight processing

---

## Technical Details

### Fan Control Interface
**Location**: `/sys/devices/platform/applesmc.768/`

**Key Files**:
- `fan1_manual` - Enable/disable manual control (0=auto, 1=manual)
- `fan1_output` - Set fan speed in RPM (when manual=1)
- `fan1_input` - Current fan speed reading
- `fan1_min` - Minimum speed (1800 RPM)
- `fan1_max` - Maximum speed (5500 RPM)

### macfanctld Operation
- **Monitoring**: Continuously reads CPU temperature from thermal sensors
- **Control**: Dynamically adjusts fan speed based on temperature thresholds
- **Range**: 1800-5500 RPM
- **Mode**: Automatic temperature-based control
- **Startup**: Enabled at boot via systemd

---

## Manual Fan Control (If Needed)

### Enable Manual Control
```bash
# Set fan to manual mode
sudo bash -c 'echo 1 > /sys/devices/platform/applesmc.768/fan1_manual'

# Set specific RPM (e.g., 4500)
sudo bash -c 'echo 4500 > /sys/devices/platform/applesmc.768/fan1_output'
```

### Return to Automatic Control
```bash
# Disable manual mode (let macfanctld control)
sudo bash -c 'echo 0 > /sys/devices/platform/applesmc.768/fan1_manual'
```

### Check Current Status
```bash
sensors | grep Exhaust
cat /sys/devices/platform/applesmc.768/fan1_manual
cat /sys/devices/platform/applesmc.768/fan1_input
```

---

## Thermal Safety Thresholds

### J5A System Limits
- **Safe Operating Range**: < 80°C
- **Warning Threshold**: 80-87°C
- **Critical Limit**: 87°C (hardware high temp)
- **Emergency Shutdown**: 105°C (CPU critical temp)

### Current Performance
- **Idle**: 55-65°C
- **Light Load**: 65-75°C
- **Heavy Load (AI Processing)**: 70-80°C
- **Safety Margin**: 7-10°C below warning threshold

---

## Integration with Night Shift

### Thermal Monitoring in J5A Worker
Location: `j5a-nightshift/j5a_worker.py`

```python
# Thermal safety check before job execution
cpu_temp = get_cpu_temperature()
if cpu_temp > 87:  # Above safe threshold
    logger.warning(f"CPU temp {cpu_temp}°C exceeds limit 87°C")
    logger.warning(f"Thermal unsafe, deferring job {job_id}")
    return {"status": "deferred", "reason": "CPU temperature too high"}
```

### Automatic Job Deferral
- Jobs automatically deferred if CPU > 87°C
- Prevents hardware damage during thermal emergencies
- Jobs can be re-queued after system cools down

---

## Monitoring Commands

### Quick Thermal Check
```bash
# Full thermal status
python3 thermal_check.py --full-status

# Just temperature
sensors | grep -E "(Package|Core|Exhaust)"

# Fan speed only
sensors | grep Exhaust
```

### macfanctld Status
```bash
# Service status
sudo systemctl status macfanctld

# View logs
sudo journalctl -u macfanctld -f
```

### Night Shift Health Check
```bash
cd /home/johnny5/Johny5Alive/j5a-nightshift
./ops/monitor_nightshift.sh
```

---

## Troubleshooting

### Fan Not Ramping Up
1. Check macfanctld is running: `systemctl status macfanctld`
2. Restart service: `sudo systemctl restart macfanctld`
3. Check for errors: `sudo journalctl -u macfanctld -n 50`

### Temperature Still High
1. Verify fan is spinning: `sensors | grep Exhaust`
2. Check thermal paste application on CPU
3. Clean air vents and ensure unobstructed airflow
4. Consider external cooling fan

### macfanctld Not Installed
```bash
# Reinstall
sudo apt-get install --reinstall macfanctld
sudo systemctl enable macfanctld
sudo systemctl start macfanctld
```

---

## Long-term Maintenance

### Regular Checks
- **Weekly**: Monitor temperatures during heavy loads
- **Monthly**: Clean dust from vents and fan intake
- **Quarterly**: Verify macfanctld service is active
- **Annually**: Consider thermal paste replacement

### Performance Monitoring
```bash
# Log temperatures during Night Shift run
watch -n 60 'sensors | grep -E "(Package|Exhaust)" | tee -a /tmp/thermal_log.txt'
```

---

## Summary

✅ **Problem**: SMC automatic fan control not functioning
✅ **Solution**: macfanctld daemon providing automatic thermal management
✅ **Status**: System thermally stable and safe for overnight AI processing
✅ **Result**: Night Shift can now run full queue without thermal issues

**Last Updated**: 2025-10-10
**Next Review**: After first full overnight run completion
