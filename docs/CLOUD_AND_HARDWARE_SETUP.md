# Real WAN validation and optional hardware

## What you actually need

For a real WAN study, the existing PC is the edge device and a remote Linux virtual machine is the cloud. A simulated sensor is sufficient to evaluate the queue/MQTT method. A physical sensor is only required to claim physical-device validation, or if specifically required by the instructor. Do not purchase hardware solely to hide this limitation.

Cloud account access and the provider are required to choose an available VM. No resource has been purchased/provisioned by these scripts. Before provisioning, check the account's current free-tier eligibility, region availability and total cost, including disks and public IP charges. Existing VMs are preferable. Keep the experimental attack topology local; do not run the baseline flood against a public cloud endpoint.

## Remote host setup (Ubuntu, when a VM is available)

Use a Linux VM reachable by SSH. Run on that VM:

```bash
sudo apt-get update
sudo apt-get install -y mosquitto python3-venv git
git clone --branch research/phase2-reproduction https://github.com/SMR202/dt-mqtt-resilience.git
cd dt-mqtt-resilience
python3 -m venv .venv
.venv/bin/pip install paho-mqtt==2.1.0
# Do not replace an existing broker's configuration. Start this dedicated
# broker only if 127.0.0.1:18886 is unused; otherwise choose another local port.
mosquitto -c configs/mosquitto-cloud.conf
```

The supplied listener binds only to localhost. Allow inbound SSH from the edge IP; do not open public MQTT port 18886. In another VM terminal:

```bash
cd dt-mqtt-resilience
.venv/bin/python scripts/cloud_endpoint.py --run wan-fifo-q1-s0 --output work/cloud-wan-fifo-q1-s0.sqlite
```

On the edge PC, establish an SSH tunnel with your existing SSH host name:

```text
ssh -N -L 18885:127.0.0.1:18886 YOUR_EXISTING_SSH_HOST
```

Then in the research repository on Windows:

```powershell
.venv\Scripts\python scripts/cloud_edge.py --run wan-fifo-q1-s0 --policy fifo --qos 1 --output work/wan-fifo-q1-s0
```

Repeat with unique run IDs for FIFO/latest × QoS 0/1/2 × at least five repetitions. Start the matching cloud receiver first each time. Counterbalance policy order. Copy the closed receiver database and edge evidence back into one experiment directory; never reuse session IDs/databases. Record VM region/type, host clocks, provider, Internet connection, start/end UTC, packet captures and SSH tunnel RTT. Record actual cloud charges if relevant.

The prepared script withholds edge dispatch from second 20 to 30. This is an application withholding interval; it is not a claimed ISP/WAN outage. SSH multiplexing adds transport overhead and head-of-line behavior; disclose that the WAN path is MQTT-over-SSH.

## Clock and metric integrity

One-way age/latency depends on clock offset. Before and after every run, collect `timedatectl` and time-synchronization status on the cloud and edge. Estimate remote UTC offset with multiple timestamp requests over SSH, recording RTT bounds; the minimum-RTT estimate has uncertainty of at least half the RTT plus server timing error. Prefer NTP-synchronized hosts with logged offset/error bounds. Do not call `received_utc-generated_utc` accurate latency without that evidence. Analyze receiver events with an event-integral AoI calculation, disclose offset sensitivity, and separate receipt ratio, sequence regressions and elapsed recovery metrics that require less clock alignment. The current cloud receiver records raw timestamps and does not certify synchronization or production restart guarantees.

## Optional ESP32 + DHT22

If physical validation is needed: ESP32 development board, DHT22 temperature/humidity sensor, USB data cable, breadboard/jumpers and a 10k pull-up resistor for a bare sensor. Use 3.3V, shared ground and GPIO4 for DATA. A module may already contain the resistor; check its actual pinout. The prepared firmware is `hardware/esp32_dht22/esp32_dht22.ino`, using the Adafruit DHT library. Physical execution is untested until the board is available.

Flash the firmware, check serial readings at 115200 baud, and close the serial monitor before the edge script. Install `pyserial==3.5` in the local experiment environment. Run:

```powershell
.venv\Scripts\python scripts/cloud_edge.py --run physical-latest-q1-s0 --policy latest --qos 1 --serial-port COM5 --output work/physical-latest-q1-s0
```

Replace COM5 with the actual board port. A DHT22 emits approximately one reading every 2.1 seconds; it does not reproduce the synthetic 20Hz workload. The edge timestamps USB arrival, not exact sensor capture. Preserve device millisecond counters/raw readings, validate units against a known reference, and disclose capture-time/serial/clock uncertainty. Temperature values are real measurements only after this procedure runs; no physical results are supplied now.
